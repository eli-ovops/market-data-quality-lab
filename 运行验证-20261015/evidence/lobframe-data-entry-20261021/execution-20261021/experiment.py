"""Independent fixed-protocol research implementation, 2026-10-21.

Written from the approved experiment specification, not LOBFrame source.
This is a historical quote simulation, not an exchange/order interface.
Stages are deliberately separate: prepare -> fit -> predict+seal -> score.
"""
import os
for _name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "6"
import argparse
from array import array
import csv
import datetime as dt
import gzip
import hashlib
import json
import math
from pathlib import Path
import random
import resource
import sys
import time

import numpy as np
import torch
from torch import nn
from torch.nn import functional as F

ROOT = Path(__file__).resolve().parent
PLAN = ROOT.parent / "十档盘口-一次历史留出验证方案-20261021.md"
PLAN_HASH = "c2921f29c37f3d24534d7ef4f88e7df0e25695f5cae581ca958b1a11c2dd089d"
TRAIN = ["2026-01-01", "2026-02-01", "2026-03-01"]
VALID = ["2026-04-01"]
TEST = ["2026-05-01", "2026-06-01", "2026-07-01", "2026-08-01", "2026-09-01"]
SEED = 20261021
MICRO = 1_000_000
START = int(dt.datetime(2026, 10, 21, 5, 28, 59, tzinfo=dt.timezone.utc).timestamp())
ACTIVE_DEADLINE = START + 6 * 3600
torch.set_num_threads(6)
torch.set_num_interop_threads(1)
torch.use_deterministic_algorithms(True)
PROCESS_START = time.time()
PHASE_KEY = str(os.getpid()) + "-" + str(time.time_ns())


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def tensor_digest(tensor):
    a = np.ascontiguousarray(tensor)
    return hashlib.sha256(memoryview(a).cast("B")).hexdigest()


def write_json(name, obj):
    path = ROOT / name
    with open(path.with_suffix(path.suffix + ".tmp"), "w") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write("\n")
    os.replace(path.with_suffix(path.suffix + ".tmp"), path)


def log(event, **fields):
    record = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(), "event": event, **fields}
    with open(ROOT / "execution-events.jsonl", "a") as f:
        f.write(json.dumps(record, ensure_ascii=False, allow_nan=False) + "\n")
    print(json.dumps(record, ensure_ascii=False, allow_nan=False), flush=True)


def budget(stage):
    r = resource.getrusage(resource.RUSAGE_SELF)
    rss = r.ru_maxrss if sys.platform == "darwin" else r.ru_maxrss * 1024
    disk = sum(p.stat().st_size for p in ROOT.rglob("*") if p.is_file())
    ledger_path = ROOT / "model-stage-ledger.json"
    ledger = json.loads(ledger_path.read_text()) if ledger_path.exists() else {}
    ledger[PHASE_KEY] = {"stage": stage, "compute_wall_s": time.time() - PROCESS_START,
                         "cpu_s": r.ru_utime + r.ru_stime, "peak_rss_bytes": rss}
    compute_wall = 104 + sum(row["compute_wall_s"] for row in ledger.values())
    write_json("model-stage-ledger.json", ledger)
    obj = {"stage": stage, "utc_epoch": time.time(), "unit_start": START,
           "unit_elapsed_wall_s": time.time() - START,
           "process_wall_s": time.time() - PROCESS_START,
           "process_user_s": r.ru_utime, "process_system_s": r.ru_stime,
           "process_peak_rss_bytes": rss, "unit_disk_bytes": disk,
           "threads": torch.get_num_threads(), "data_qc_wall_s_conservative": 104,
           "cumulative_compute_wall_s": compute_wall, "compute_wall_cap_s": 7200,
           "active_work_deadline_epoch": ACTIVE_DEADLINE}
    write_json("model-budget-receipt.json", obj)
    # Reserve 30s for the current bounded batch group and orderly STOP receipt.
    if rss > 4 * 1024**3 or disk > 1024**3 or compute_wall >= 7170 or time.time() >= ACTIVE_DEADLINE:
        raise RuntimeError("TECHNICAL_STOP: resource cap reached")
    return obj


def seed():
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)


class ConvUnit(nn.Module):
    def __init__(self, incoming, outgoing, kernel, stride=(1, 1), temporal_pad=False):
        super().__init__()
        self.pad = ((kernel[0] - 1) // 2, kernel[0] // 2) if temporal_pad else (0, 0)
        self.conv = nn.Conv2d(incoming, outgoing, kernel, stride=stride, padding=0, bias=True)
        self.activation = nn.LeakyReLU(0.01)
        self.norm = nn.BatchNorm2d(outgoing, eps=1e-5, momentum=0.1, affine=True, track_running_stats=True)

    def forward(self, x):
        if self.pad != (0, 0):
            x = F.pad(x, (0, 0, self.pad[0], self.pad[1]))
        return self.norm(self.activation(self.conv(x)))


class QuoteRegressor(nn.Module):
    def __init__(self):
        super().__init__()
        stages = []
        for incoming, width in ((1, 2), (32, 2), (32, 10)):
            step = (1, 2) if width == 2 else (1, 1)
            stages.append(nn.Sequential(
                ConvUnit(incoming, 32, (1, width), step),
                ConvUnit(32, 32, (4, 1), temporal_pad=True),
                ConvUnit(32, 32, (4, 1), temporal_pad=True)))
        self.spatial = nn.Sequential(*stages)
        self.branches = nn.ModuleList([
            nn.Sequential(ConvUnit(32, 64, (1, 1)), ConvUnit(64, 64, (3, 1), temporal_pad=True)),
            nn.Sequential(ConvUnit(32, 64, (1, 1)), ConvUnit(64, 64, (5, 1), temporal_pad=True)),
            nn.Sequential(nn.MaxPool2d((3, 1), stride=(1, 1), padding=(1, 0)), ConvUnit(32, 64, (1, 1)))])
        self.sequence = nn.LSTM(192, 64, num_layers=1, batch_first=True, dropout=0, bidirectional=False)
        self.output = nn.Linear(64, 1, bias=True)

    def forward(self, x):
        spatial = self.spatial(x)
        merged = torch.cat([branch(spatial) for branch in self.branches], dim=1)
        sequence = merged.squeeze(-1).transpose(1, 2).contiguous()
        encoded, _ = self.sequence(sequence)  # independent zero initial state each call
        return self.output(encoded[:, -1, :]).squeeze(-1)


def state_digest(model):
    h = hashlib.sha256()
    for name, value in model.state_dict().items():
        h.update(name.encode())
        h.update(value.detach().cpu().numpy().tobytes())
    return h.hexdigest()


def source_path(day):
    # Identity receipt is the admission gate. It is read, never modified here.
    receipt = ROOT / "data-receipt.json"
    if not receipt.is_file():
        raise RuntimeError("DATA_NOT_ADMITTED: missing data-receipt.json")
    admission = json.loads(receipt.read_text())
    if admission["status"] != "PASS_ALL_NINE_FILE_QC" or admission["protocol_sha256_verified_before_get"] != PLAN_HASH:
        raise RuntimeError("DATA_NOT_ADMITTED: data QC/protocol gate failed")
    candidates = [row for row in admission["files"] if row["date"] == day]
    if len(candidates) != 1:
        raise RuntimeError(f"DATA_NOT_ADMITTED: expected one admitted gzip for {day}")
    row = candidates[0]
    path = Path(row["path"])
    if not path.is_relative_to(ROOT / "data") or digest(path) != row["compressed_sha256"]:
        raise RuntimeError("DATA_NOT_ADMITTED: source path/hash changed")
    return path


class DayBook:
    def __init__(self, day):
        self.day = day
        self.path = source_path(day)
        self.source_sha256 = digest(self.path)
        ts = array("q")
        values = array("d")
        fields = [f"{side}[{j}].{field}" for j in range(10)
                  for side in ("asks", "bids") for field in ("price", "amount")]
        raw_rows = 0
        with gzip.open(self.path, "rt", newline="") as f:
            reader = csv.reader(f)
            header = next(reader)
            ti = header.index("local_timestamp")
            positions = [header.index(k) for k in fields]
            last = -1
            for row in reader:
                raw_rows += 1
                t = int(row[ti])
                if t < last:
                    raise RuntimeError(f"TECHNICAL_STOP: nonmonotonic local clock {day}")
                v = [float(row[k]) if row[k] else float("nan") for k in positions]
                if t == last:
                    del values[-40:]
                    values.extend(v)
                else:
                    ts.append(t)
                    values.extend(v)
                last = t
        self.ts = np.frombuffer(ts, dtype=np.int64)
        self.v = np.frombuffer(values, dtype=np.float64).reshape(-1, 40)
        self.base = int(dt.datetime.fromisoformat(day).replace(tzinfo=dt.timezone.utc).timestamp()) * MICRO
        if len(self.ts) == 0 or self.ts[0] < self.base or self.ts[-1] >= self.base + 86400 * MICRO:
            raise RuntimeError(f"TECHNICAL_STOP: day boundary {day}")
        asks = self.v[:, 0::4]
        bids = self.v[:, 2::4]
        self.valid = (np.isfinite(self.v).all(axis=1) & (self.v > 0).all(axis=1)
                      & (np.diff(asks, axis=1) > 0).all(axis=1)
                      & (np.diff(bids, axis=1) < 0).all(axis=1)
                      & (asks[:, 0] >= bids[:, 0]))
        self.bad_prefix = np.r_[0, np.cumsum(~self.valid)]
        self.gap_prefix = np.r_[0, np.cumsum(np.r_[False, np.diff(self.ts) > 2 * MICRO])]
        self.raw_rows = raw_rows

    def candidates(self, stride):
        # inclusive fixed end 23:53; train/validation use the same fixed bounds
        return self.base + np.arange(300, 23 * 3600 + 53 * 60 + 1, stride, dtype=np.int64) * MICRO

    def known_input(self, t):
        end = int(np.searchsorted(self.ts, t, side="right")) - 1
        start = end - 99
        if start < 0:
            return None, "fewer_than_100_states"
        if t - self.ts[end] > MICRO:
            return None, "last_state_stale"
        if self.bad_prefix[end + 1] != self.bad_prefix[start]:
            return None, "input_invalid_state"
        if self.gap_prefix[end + 1] != self.gap_prefix[start + 1]:
            return None, "input_gap_over_2s"
        return (start, end), None

    def transform(self, bounds):
        start, end = bounds
        x = self.v[start:end + 1].copy()
        anchor = (self.v[end, 0] + self.v[end, 2]) / 2
        x[:, 0::2] = np.log(x[:, 0::2] / anchor)
        x[:, 1::2] = np.log1p(x[:, 1::2])
        return x.astype(np.float32)

    def future(self, t, delay=1):
        # Called only for training/validation or after ALL test predictions seal.
        ia = int(np.searchsorted(self.ts, t + delay * MICRO, side="left"))
        ib = int(np.searchsorted(self.ts, t + (delay + 60) * MICRO, side="left"))
        if ia >= len(self.ts) or ib >= len(self.ts):
            return None, "missing_first_quote"
        if self.ts[ia] > t + (delay + 1) * MICRO or self.ts[ib] > t + (delay + 61) * MICRO:
            return None, "quote_wait_over_1s"
        begin = max(0, int(np.searchsorted(self.ts, t, side="right")) - 1)
        if self.bad_prefix[ib + 1] != self.bad_prefix[begin]:
            return None, "future_invalid_state"
        if self.gap_prefix[ib + 1] != self.gap_prefix[begin + 1]:
            return None, "future_gap_over_2s"
        return (ia, ib), None


def sample_days(days, with_targets):
    xs, ys, identities, counts = [], [], [], {}
    for day in days:
        book = DayBook(day)
        count = {"candidate": 0, "known_input": 0, "training_target_available": 0, "reasons": {}}
        for t in book.candidates(10):
            count["candidate"] += 1
            bounds, reason = book.known_input(int(t))
            if bounds is None:
                count["reasons"][reason] = count["reasons"].get(reason, 0) + 1
                continue
            count["known_input"] += 1
            future, reason = book.future(int(t)) if with_targets else (None, None)
            if with_targets and future is None:
                key = "target_" + reason
                count["reasons"][key] = count["reasons"].get(key, 0) + 1
                continue
            xs.append(book.transform(bounds))
            if with_targets:
                ia, ib = future
                ys.append(10000 * math.log(book.v[ib, 2] / book.v[ia, 0]))
            identities.append({"day": day, "t": int(t), "start_row": bounds[0], "end_row": bounds[1],
                               "last_input_timestamp": int(book.ts[bounds[1]]), "source_sha256": book.source_sha256})
            count["training_target_available"] += int(with_targets)
        counts[day] = count
        log("sample_day", day=day, counts=count)
        budget("preparing")
    if not xs:
        raise RuntimeError("TECHNICAL_STOP: no admitted samples")
    x = np.stack(xs)
    return x, np.asarray(ys, dtype=np.float64), identities, counts


def prepare():
    if (ROOT / "training-input-seal.json").exists():
        raise RuntimeError("Refuse overwrite of training input seal")
    x, y, ids, counts = sample_days(TRAIN, True)
    mean = np.mean(x, axis=(0, 1), dtype=np.float64)
    var = np.var(x, axis=(0, 1), dtype=np.float64)
    sd = np.sqrt(var)
    sd[sd == 0] = 1
    ym, ys = float(y.mean()), float(y.std(ddof=0))
    if not ys > 0 or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise RuntimeError("TECHNICAL_STOP: degenerate/nonfinite training statistics")
    stats = {"input_mean": mean.tolist(), "input_std": sd.tolist(), "target_mean": ym, "target_std": ys,
             "ddof": 0, "window_cells_repeated": True, "training_samples": len(y)}
    write_json("training-statistics.json", stats)
    write_json("training-samples.json", ids)
    write_json("training-input-seal.json", {"plan_sha256": digest(PLAN), "implementation_sha256": digest(__file__),
               "data_receipt_sha256": digest(ROOT / "data-receipt.json"), "counts": counts,
               "raw_transformed_input_sha256": tensor_digest(x), "target_bp_sha256": tensor_digest(y),
               "statistics_sha256": digest(ROOT / "training-statistics.json"),
               "samples_sha256": digest(ROOT / "training-samples.json")})
    log("training_input_sealed", samples=len(y), target_std=ys, budget=budget("prepared"))


def normalized(x, stats):
    return ((x - np.asarray(stats["input_mean"], dtype=np.float32)) /
            np.asarray(stats["input_std"], dtype=np.float32)).astype(np.float32)


def batches(x, indices, mask):
    for start in range(0, len(indices), 64):
        idx = indices[start:start + 64]
        values = x[idx].copy()
        if mask:
            values[:, :, 4:] = 0
        yield idx, torch.from_numpy(values).unsqueeze(1)


def inference(model, x, mask):
    model.eval()
    out = []
    with torch.no_grad():
        for number, (_, values) in enumerate(batches(x, np.arange(len(x)), mask)):
            out.append(model(values).numpy())
            if number % 20 == 0:
                budget("frozen_eval")
    result = np.concatenate(out)
    if not np.isfinite(result).all():
        raise RuntimeError("TECHNICAL_STOP: nonfinite model predictions")
    return result.astype(np.float64)


def fit():
    if (ROOT / "fit-started.json").exists():
        raise RuntimeError("TECHNICAL_STOP: fixed fit already started, rerun forbidden")
    seal = json.loads((ROOT / "training-input-seal.json").read_text())
    if seal["implementation_sha256"] != digest(__file__) or seal["plan_sha256"] != digest(PLAN):
        raise RuntimeError("TECHNICAL_STOP: implementation/protocol changed after input seal")
    for filename, field in (("training-statistics.json", "statistics_sha256"),
                            ("training-samples.json", "samples_sha256"),
                            ("data-receipt.json", "data_receipt_sha256")):
        if digest(ROOT / filename) != seal[field]:
            raise RuntimeError("TECHNICAL_STOP: prepared artifact identity changed")
    stats = json.loads((ROOT / "training-statistics.json").read_text())
    x, y, _, _ = sample_days(TRAIN, True)
    if tensor_digest(x) != seal["raw_transformed_input_sha256"] or tensor_digest(y) != seal["target_bp_sha256"]:
        raise RuntimeError("TECHNICAL_STOP: training input identity changed")
    x = normalized(x, stats)
    target = ((y - stats["target_mean"]) / stats["target_std"]).astype(np.float32)
    vx, vy, _, vcounts = sample_days(VALID, True)
    vx = normalized(vx, stats)
    write_json("fit-started.json", {"utc": dt.datetime.now(dt.timezone.utc).isoformat(), "implementation_sha256": digest(__file__), "one_fit_per_model": True})
    init_hash = None
    fits = {}
    for name in ("A", "B"):
        seed()
        model = QuoteRegressor()
        current_hash = state_digest(model)
        if init_hash is None:
            init_hash = current_hash
        assert init_hash == current_hash
        optimizer = torch.optim.Adam(model.parameters(), lr=0.001, betas=(0.9, 0.999), eps=1e-8, weight_decay=0)
        permutations = np.random.default_rng(SEED)
        perm_hash = hashlib.sha256()
        for epoch in range(20):
            model.train()
            order = permutations.permutation(len(x))
            perm_hash.update(order.astype(np.int64).tobytes())
            total, seen = 0.0, 0
            for number, (idx, values) in enumerate(batches(x, order, name == "A")):
                optimizer.zero_grad(set_to_none=True)
                prediction = model(values)
                loss = F.mse_loss(prediction, torch.from_numpy(target[idx]))
                if not torch.isfinite(loss):
                    raise RuntimeError("TECHNICAL_STOP: nonfinite training loss")
                loss.backward()
                norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0, error_if_nonfinite=True)
                optimizer.step()
                total += float(loss.detach()) * len(idx)
                seen += len(idx)
                if number % 20 == 0:
                    budget(f"fit_{name}_epoch_{epoch + 1}")
            log("epoch", model=name, epoch=epoch + 1, batch_loss_standardized=total / seen, budget=budget("fitting"))
        # Final weight only; no checkpoint selection or retries.
        model.eval()
        torch.save(model.state_dict(), ROOT / f"weights-{name}.pt")
        train_hat = inference(model, x, name == "A") * stats["target_std"] + stats["target_mean"]
        val_hat = inference(model, vx, name == "A") * stats["target_std"] + stats["target_mean"]
        train_mse = float(np.mean((train_hat - y)**2))
        baseline_mse = float(np.mean((y - stats["target_mean"])**2))
        record = {"model": name, "initial_parameters_sha256": current_hash,
                  "epoch_permutations_sha256": perm_hash.hexdigest(), "epochs": 20,
                  "weight_sha256": digest(ROOT / f"weights-{name}.pt"),
                  "train_eval_mse_bp2": train_mse, "train_mean_baseline_mse_bp2": baseline_mse,
                  "validation_eval_mse_bp2": float(np.mean((val_hat - vy)**2)),
                  "validation_counts": vcounts, "training_capability_pass": train_mse < baseline_mse}
        write_json(f"fit-{name}.json", record)
        fits[name] = record
        log("fit_final", **record)
        if not record["training_capability_pass"]:
            raise RuntimeError(f"TECHNICAL_STOP: {name} cannot beat training mean, test forbidden")
        del optimizer, model
    assert fits["A"]["epoch_permutations_sha256"] == fits["B"]["epoch_permutations_sha256"]
    write_json("weights-seal.json", {"fits": fits, "stats_sha256": digest(ROOT / "training-statistics.json"),
                                   "implementation_sha256": digest(__file__), "budget": budget("weights_sealed")})


def predict():
    if not (ROOT / "weights-seal.json").exists() or (ROOT / "predictions-seal.json").exists():
        raise RuntimeError("TECHNICAL_STOP: weights not sealed or predictions already sealed")
    weight_seal = json.loads((ROOT / "weights-seal.json").read_text())
    if weight_seal["implementation_sha256"] != digest(__file__) or weight_seal["stats_sha256"] != digest(ROOT / "training-statistics.json"):
        raise RuntimeError("TECHNICAL_STOP: weight seal implementation/statistics drift")
    for name in ("A", "B"):
        if weight_seal["fits"][name]["weight_sha256"] != digest(ROOT / f"weights-{name}.pt"):
            raise RuntimeError("TECHNICAL_STOP: sealed weight identity changed")
    stats = json.loads((ROOT / "training-statistics.json").read_text())
    models = {}
    for name in ("A", "B"):
        m = QuoteRegressor()
        m.load_state_dict(torch.load(ROOT / f"weights-{name}.pt", map_location="cpu", weights_only=True))
        m.eval()
        models[name] = m
    sealed = {}
    for day in TEST:
        book = DayBook(day)
        xs, rows, absent = [], [], []
        for t in book.candidates(120):
            bounds, reason = book.known_input(int(t))
            if bounds is None:
                absent.append({"t": int(t), "reason": reason})
                continue
            xs.append(book.transform(bounds))
            rows.append({"t": int(t), "start_row": bounds[0], "end_row": bounds[1],
                         "last_input_timestamp": int(book.ts[bounds[1]]),
                         "C": 10000 * math.log(book.v[bounds[1], 2] / book.v[bounds[1], 0])})
        if xs:
            x = normalized(np.stack(xs), stats)
            for name, m in models.items():
                output = inference(m, x, name == "A") * stats["target_std"] + stats["target_mean"]
                for row, value in zip(rows, output):
                    row[name] = float(value)
        payload = {"day": day, "source_sha256": book.source_sha256, "candidate_count": 715,
                   "known_input_count": len(rows), "known_input_unavailable": absent, "predictions": rows,
                   "future_target_accessed": False, "weights_seal_sha256": digest(ROOT / "weights-seal.json")}
        filename = f"predictions-{day}.json"
        if (ROOT / filename).exists():
            raise RuntimeError("TECHNICAL_STOP: refuse overwrite prediction artifact")
        write_json(filename, payload)
        sealed[filename] = digest(ROOT / filename)
        log("day_predictions_sealed", day=day, known_input_count=len(rows), budget=budget("predicting"))
    write_json("predictions-seal.json", {"utc": dt.datetime.now(dt.timezone.utc).isoformat(), "files": sealed,
                  "weight_seal_sha256": digest(ROOT / "weights-seal.json"), "implementation_sha256": digest(__file__),
                  "all_five_days_sealed_before_scoring": True, "budget": budget("predictions_sealed")})


def buy_depth(snapshot, budget_cash, fee, slip):
    """Spend the entire fee-inclusive budget; reject insufficient visible depth."""
    left, qty, raw_notional = budget_cash, 0.0, 0.0
    for price, available in zip(snapshot[0::4], snapshot[1::4]):
        take = min(float(available), left / (price * (1 + slip) * (1 + fee)))
        raw_notional += take * price
        qty += take
        left -= take * price * (1 + slip) * (1 + fee)
        if left <= max(1e-9, budget_cash * 1e-12):
            execution = raw_notional * (1 + slip)
            return {"quantity": qty, "raw_notional": raw_notional, "execution_notional": execution,
                    "slippage_cost": raw_notional * slip, "fee": execution * fee,
                    "cash_out": execution * (1 + fee)}
    return None


def sell_depth(snapshot, qty, fee, slip):
    left, raw_notional = qty, 0.0
    for price, available in zip(snapshot[2::4], snapshot[3::4]):
        take = min(float(available), left)
        raw_notional += take * price
        left -= take
        if left <= max(1e-12, qty * 1e-12):
            execution = raw_notional * (1 - slip)
            return {"quantity": qty, "raw_notional": raw_notional, "execution_notional": execution,
                    "slippage_cost": raw_notional * slip, "fee": execution * fee,
                    "cash_in": execution * (1 - fee)}
    return None


def scenario(name, fee_bp, delay, predictions, books):
    fee, slip = fee_bp / 10000, 0.0001
    threshold = 10000 * math.log((1 + slip) * (1 + fee) / ((1 - slip) * (1 - fee)))
    cash = 5000.0
    transactions, day_results, missing, equity_records = [], [], [], []
    fees, slippages, minute_returns = 0.0, 0.0, []
    for day in TEST:
        book = books[day]
        initial = cash
        local_trades = []
        for row in predictions[day]["predictions"]:
            if row[name] <= threshold:
                continue
            t = row["t"]
            future, reason = book.future(t, delay)
            if future is None:
                missing.append({"day": day, "t": t, "reason": reason})
                # Cash after an unknown trade is not known. Do not fabricate later trades.
                break
            ia, ib = future
            spend = min(cash * 0.1, 500.0)
            bought = buy_depth(book.v[ia], spend, fee, slip)
            sold = sell_depth(book.v[ib], bought["quantity"], fee, slip) if bought else None
            if bought is None or sold is None:
                missing.append({"day": day, "t": t, "reason": "insufficient_ten_level_depth"})
                break
            before = cash
            cash -= bought["cash_out"]
            after_entry = cash
            cash += sold["cash_in"]
            if cash < -1e-8 or bought["cash_out"] > before + 1e-8:
                raise RuntimeError("TECHNICAL_STOP: cash conservation violation")
            tr = {"day": day, "decision_timestamp": t, "prediction_bp": row[name], "threshold_bp": threshold,
                  "entry_timestamp": int(book.ts[ia]), "exit_timestamp": int(book.ts[ib]),
                  "entry_row": ia, "exit_row": ib, "source_sha256": book.source_sha256,
                  "cash_before": before, "budget_including_entry_fee": spend, "cash_after_entry": after_entry,
                  "cash_after_exit": cash, "quantity_btc": bought["quantity"],
                  "buy": bought, "sell": sold, "net_pnl": cash - before,
                  "holding_seconds": (int(book.ts[ib]) - int(book.ts[ia])) / MICRO}
            transactions.append(tr)
            local_trades.append(tr)
            fees += bought["fee"] + sold["fee"]
            slippages += bought["slippage_cost"] + sold["slippage_cost"]
        if missing:
            break
        # Mark equity using last <= minute quote, never future quote.
        day_equity = []
        day_risk_missing = []
        cursor, completed_cash = 0, initial
        for second in range(300, 23 * 3600 + 55 * 60 + 1, 60):
            t = book.base + second * MICRO
            while cursor < len(local_trades) and local_trades[cursor]["exit_timestamp"] <= t:
                completed_cash = local_trades[cursor]["cash_after_exit"]
                cursor += 1
            active = local_trades[cursor] if cursor < len(local_trades) and local_trades[cursor]["entry_timestamp"] <= t else None
            eq = completed_cash
            reason = None
            mark_row = None
            if active is not None:
                mark_row = int(np.searchsorted(book.ts, t, side="right")) - 1
                if mark_row < 0 or t - book.ts[mark_row] > MICRO or not book.valid[mark_row]:
                    reason = "minute_quote_stale_or_invalid"
                else:
                    liquidation = sell_depth(book.v[mark_row], active["quantity_btc"], fee, slip)
                    if liquidation is None:
                        reason = "minute_insufficient_depth"
                    else:
                        eq = active["cash_after_entry"] + liquidation["cash_in"]
            if reason:
                day_risk_missing.append({"t": t, "reason": reason})
                day_equity.append(None)
            else:
                day_equity.append(eq)
            equity_records.append({"day": day, "timestamp": t, "equity": None if reason else eq,
                                   "active_trade_decision": None if active is None else active["decision_timestamp"],
                                   "mark_row": mark_row, "reason": reason})
        if not day_risk_missing:
            minute_returns.extend(np.diff(np.log(np.asarray(day_equity))).tolist())
        day_results.append({"day": day, "cash_start": initial, "cash_end": cash, "net_pnl": cash - initial,
                            "closed_trades": len(local_trades), "risk_missing": day_risk_missing})
        budget("economic_accounting")
    complete = not missing and len(day_results) == 5
    risk_missing = any(row["risk_missing"] for row in day_results)
    risk = float(np.std(minute_returns, ddof=1)) if complete and not risk_missing and len(minute_returns) > 1 else None
    complete_equity = [r["equity"] for r in equity_records if r["equity"] is not None]
    drawdown = None
    if complete and not risk_missing:
        a = np.asarray(complete_equity)
        drawdown = float(np.max(1 - a / np.maximum.accumulate(a)))
    if complete:
        assert math.isclose(sum(d["net_pnl"] for d in day_results), cash - 5000, abs_tol=1e-7)
    key = f"{name}-fee{fee_bp}-delay{delay}"
    write_json(f"trades-{key}.json", transactions)
    write_json(f"minute-equity-{key}.json", equity_records)
    result = {"model": name, "fee_bp_per_side": fee_bp, "slip_bp_per_side": 1, "delay_s": delay,
              "threshold_bp": threshold, "complete_economic_ledger": complete,
              "final_cash": cash if complete else None, "net_pnl": cash - 5000 if complete else None,
              "last_known_cash_before_missing_trade": cash if not complete else None,
              "closed_trades": len(transactions), "fees_usd": fees, "extra_slippage_usd": slippages,
              "daily": day_results, "selected_trade_missing": missing, "minute_risk_sd": risk,
              "minute_max_drawdown": drawdown,
              "holding_seconds_sum": sum(t["holding_seconds"] for t in transactions)}
    write_json(f"economics-{key}.json", result)
    return result


def score():
    if not (ROOT / "predictions-seal.json").exists() or (ROOT / "scoring-started.json").exists():
        raise RuntimeError("TECHNICAL_STOP: predictions unsealed or scoring already started")
    seal = json.loads((ROOT / "predictions-seal.json").read_text())
    for path, sha in seal["files"].items():
        assert digest(ROOT / path) == sha
    assert seal["implementation_sha256"] == digest(__file__)
    write_json("scoring-started.json", {"utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                                       "predictions_seal_sha256": digest(ROOT / "predictions-seal.json")})
    predictions = {day: json.loads((ROOT / f"predictions-{day}.json").read_text()) for day in TEST}
    daily, books = [], {}
    for day in TEST:
        book = DayBook(day)
        books[day] = book
        if book.source_sha256 != predictions[day]["source_sha256"]:
            raise RuntimeError("TECHNICAL_STOP: source identity changed")
        errors = {k: [] for k in ("A", "B", "C")}
        target_rows, unavailable = [], []
        for row in predictions[day]["predictions"]:
            future, reason = book.future(row["t"])
            if future is None:
                unavailable.append({"t": row["t"], "reason": reason})
                continue
            ia, ib = future
            y = 10000 * math.log(book.v[ib, 2] / book.v[ia, 0])
            for name in errors:
                errors[name].append((row[name] - y)**2)
            target_rows.append({"t": row["t"], "entry_row": ia, "exit_row": ib,
                                "entry_timestamp": int(book.ts[ia]), "exit_timestamp": int(book.ts[ib]), "target_bp": y})
        result = {"day": day, "candidate": 715, "known_input": predictions[day]["known_input_count"],
                  "common_evaluable": len(target_rows), "future_missing": unavailable,
                  "mse_bp2": {k: float(np.mean(v)) if v else None for k, v in errors.items()}}
        daily.append(result)
        write_json(f"targets-{day}.json", target_rows)
        log("test_day_scored", day=day, common_evaluable=len(target_rows), mse_bp2=result["mse_bp2"])
    sufficient = all(d["common_evaluable"] >= 500 for d in daily)
    overall = {k: float(np.mean([d["mse_bp2"][k] for d in daily])) if all(d["mse_bp2"][k] is not None for d in daily) else None for k in ("A", "B", "C")}
    wins = sum(d["mse_bp2"]["B"] < d["mse_bp2"]["A"] for d in daily if d["mse_bp2"]["A"] is not None)
    pred_pass = sufficient and overall["B"] < overall["A"] and overall["B"] < overall["C"] and wins >= 4
    prediction_status = "INDETERMINATE" if not sufficient else "PASS" if pred_pass else "NOT_PASS"
    economics = {}
    for fee in (5, 10, 25, 50):
        for delay in (1, 5):
            for name in ("A", "B"):
                key = f"{name}-fee{fee}-delay{delay}"
                economics[key] = scenario(name, fee, delay, predictions, books)
                log("economic_scenario_complete", key=key, complete=economics[key]["complete_economic_ledger"], budget=budget("scoring"))
    a, b = economics["A-fee25-delay1"], economics["B-fee25-delay1"]
    ratio = b["minute_risk_sd"] / a["minute_risk_sd"] if a["minute_risk_sd"] and b["minute_risk_sd"] else None
    risk_comparable = ratio is not None and 0.8 <= ratio <= 1.25
    if not a["complete_economic_ledger"] or not b["complete_economic_ledger"] or b["closed_trades"] < 30:
        economic_status = "INDETERMINATE"
    elif b["net_pnl"] <= 0:
        economic_status = "NOT_PASS"
    elif not risk_comparable or a["minute_max_drawdown"] is None or b["minute_max_drawdown"] is None:
        economic_status = "INDETERMINATE"
    else:
        economic_status = "PASS" if b["net_pnl"] > a["net_pnl"] and b["minute_max_drawdown"] <= a["minute_max_drawdown"] else "NOT_PASS"
    write_json("results.json", {"daily_prediction": daily, "overall_mse_bp2_equal_day_weight": overall,
                  "B_better_than_A_days": wins, "prediction_status": prediction_status,
                  "economics": economics, "main_economic_status": economic_status,
                  "main_risk_ratio_B_over_A": ratio,
                  "historical_candidate": prediction_status == "PASS" and economic_status == "PASS",
                  "scope": "conditional historical quote/depth simulation; real fees/latency/impact/operating costs UNKNOWN",
                  "budget": budget("completed")})
    manifest = {str(p.relative_to(ROOT)): {"bytes": p.stat().st_size, "sha256": digest(p)}
                for p in ROOT.iterdir() if p.is_file() and p.name not in ("artifact-manifest.json", "model-budget-receipt.json", "execution-events.jsonl", "data-progress.json", "data-receipt.json")}
    write_json("artifact-manifest.json", manifest)
    log("experiment_completed", prediction_status=prediction_status, main_economic_status=economic_status)


def selfcheck():
    seed()
    model = QuoteRegressor()
    h = state_digest(model)
    seed()
    assert h == state_digest(QuoteRegressor())
    x = torch.randn(64, 1, 100, 40)
    started = time.perf_counter()
    model.train()
    out = model(x)
    assert out.shape == (64,)
    out.square().mean().backward()
    torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0, error_if_nonfinite=True)
    step_seconds = time.perf_counter() - started
    model.eval()
    before = state_digest(model)
    with torch.no_grad():
        y = model(x[:2])
    assert state_digest(model) == before and torch.isfinite(y).all()
    # Hand case: $500 budget, price=100 ask / 110 bid, fee=.01, slip=.001.
    snapshot = np.tile([100.0, 100.0, 110.0, 100.0], 10)
    bought = buy_depth(snapshot, 500, .01, .001)
    expected_qty = 500 / (100 * 1.001 * 1.01)
    assert math.isclose(bought["quantity"], expected_qty, rel_tol=1e-12)
    sold = sell_depth(snapshot, expected_qty, .01, .001)
    expected_cash = expected_qty * 110 * .999 * .99
    assert math.isclose(sold["cash_in"], expected_cash, rel_tol=1e-12)
    # Test exact timestamp selection, same-time last state, inclusive >=, and future mask isolation.
    assert int(np.searchsorted(np.array([100, 200, 300]), 200, side="left")) == 1
    assert int(np.searchsorted(np.array([100, 200, 300]), 200, side="right")) - 1 == 1
    book = DayBook.__new__(DayBook)
    book.ts = np.arange(250, dtype=np.int64) * MICRO
    book.v = np.tile(np.array([101 + j if k == 0 else 99 - j if k == 2 else 2
                              for j in range(10) for k in range(4)], dtype=np.float64), (250, 1))
    book.valid = np.ones(250, dtype=bool)
    book.bad_prefix = np.zeros(251, dtype=np.int64)
    book.gap_prefix = np.zeros(251, dtype=np.int64)
    bounds, reason = book.known_input(100 * MICRO)
    assert bounds == (1, 100) and reason is None
    first = book.transform(bounds)
    assert first.shape == (100, 40)
    assert math.isclose(float(first[0, 0]), math.log(101 / 100), rel_tol=1e-6)
    assert math.isclose(float(first[0, 1]), math.log1p(2), rel_tol=1e-6)
    assert book.future(100 * MICRO)[0] == (101, 161)
    assert math.isclose(10000 * math.log(book.v[161, 2] / book.v[101, 0]), 10000 * math.log(99 / 101))
    # An unobserved future defect changes label availability, not known input/features.
    book.bad_prefix[151:] = 1
    assert book.known_input(100 * MICRO)[0] == bounds
    assert np.array_equal(first, book.transform(bounds))
    assert book.future(100 * MICRO)[1] == "future_invalid_state"
    common_stats = {"input_mean": [1.] * 40, "input_std": [2.] * 40}
    normalized_case = normalized(np.stack([first]), common_stats)
    _, a = next(batches(normalized_case, np.arange(1), True))
    _, b = next(batches(normalized_case, np.arange(1), False))
    assert torch.equal(a[:, :, :, :4], b[:, :, :, :4]) and torch.count_nonzero(a[:, :, :, 4:]) == 0
    result = {"torch_version": torch.__version__, "numpy_version": np.__version__, "threads": torch.get_num_threads(),
              "model_parameters": sum(p.numel() for p in model.parameters()), "output_shape": list(out.shape),
              "same_initial_state_sha256": h, "eval_bn_unchanged": True,
              "causal_input_future_defect_isolation": True, "inclusive_target_alignment": True,
              "shared_normalization_then_A_mask": True, "synthetic_forward_backward_seconds": step_seconds,
              "estimated_two_model_fit_seconds_at_25000_samples": step_seconds * math.ceil(25000 / 64) * 40,
              "fee_hand_case": {"quantity": expected_qty, "net_exit_cash": expected_cash, "pnl": expected_cash - 500},
              "plan_sha256": digest(PLAN), "implementation_sha256": digest(__file__), "budget": budget("selfcheck")}
    write_json("selfcheck.json", result)
    log("selfcheck_passed", **result)


def main():
    if (ROOT / "technical-stop.json").exists():
        print("REFUSED: existing unit technical STOP; original receipt retained", flush=True)
        raise SystemExit(2)
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=["selfcheck", "prepare", "fit", "predict", "score"])
    args = parser.parse_args()
    if digest(PLAN) != PLAN_HASH:
        raise RuntimeError("TECHNICAL_STOP: approved plan hash mismatch")
    budget(args.stage)
    {"selfcheck": selfcheck, "prepare": prepare, "fit": fit, "predict": predict, "score": score}[args.stage]()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        log("technical_stop", type=type(exc).__name__, message=str(exc))
        if not (ROOT / "technical-stop.json").exists():
            write_json("technical-stop.json", {"type": type(exc).__name__, "message": str(exc), "utc": dt.datetime.now(dt.timezone.utc).isoformat()})
        raise
