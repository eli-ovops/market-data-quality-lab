"""One authorized E/S diagnostic; never imports or runs original experiment CLI."""
# Start deadline protection BEFORE importing numerical libraries.
import time
PROCESS_STARTED = time.monotonic()
import os
for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[key] = "6"
import ast
from array import array
import csv
import datetime as dt
import gzip
import hashlib
import json
import math
from pathlib import Path
import resource
import signal
import sys
import types

OUT = Path(__file__).resolve().parent
UNIT = OUT.parent
OLD = UNIT.parent / "execution-20261021"
PLAN = OLD / "diagnosis-readonly/root/封存A权重-一次模式归因诊断方案.md"
PLAN_SHA = "d44254502356e37c190ebb25f561ebd9a54e8fddbcc4b7e5ae30857cc4167fb8"
SOURCE_SHA = "148a44f30da8966d7fa076ea7f152ed3396f936be0a8d800c810f388bdefdf05"
DEADLINE = dt.datetime(2026, 10, 21, 9, 10, 22, tzinfo=dt.timezone.utc).timestamp()
TRAIN = ["2026-01-01", "2026-02-01", "2026-03-01"]
EXPECTED_HASHES = {
    "experiment.py": SOURCE_SHA,
    "weights-A.pt": "fa200c539704f1e78d69c47519980947c589dba1d5e5ea72a6a40cf89e5aa637",
    "training-statistics.json": "0eba2fb103b27c209a4401c7fa8af5715ecfe71293f2ba579e251beff78e49b1",
    "training-samples.json": "1c1f80bc035ee6027a2554961ad82e035ba12d305cc0567b3e4dde50f33ea23e",
    "technical-stop.json": "6f37b1f1de6441500181531e4ac9acf570145a35cfc9cea9dfdcfcd90317bc1e"}
PURE_NAMES = {"digest", "tensor_digest", "ConvUnit", "QuoteRegressor", "state_digest", "source_path",
              "DayBook", "sample_days", "normalized", "batches"}


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def save(name, data):
    path = OUT / name
    if path.exists():
        raise RuntimeError("refuse evidence overwrite: " + name)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def fail(reason):
    path = OUT / "terminal-stop.json"
    if not path.exists():
        path.write_text(json.dumps({"utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                                   "reason": reason, "wall_s": time.monotonic() - PROCESS_STARTED}, indent=2) + "\n")


def alarm_handler(signum, frame):
    raise TimeoutError("600s cumulative diagnostic process deadline or active-work deadline")


signal.signal(signal.SIGALRM, alarm_handler)
if (OUT / "run-started.json").exists() or (OUT / "terminal-stop.json").exists():
    raise SystemExit("REFUSED: this new unit already started/stopped; rerun forbidden")
prior_static = json.loads((OUT / "static-preflight.json").read_text())["static_helper_wall_s"]
remaining = min(600 - prior_static - (time.monotonic() - PROCESS_STARTED), DEADLINE - time.time())
if remaining <= 0:
    raise SystemExit("REFUSED: diagnostic budget exhausted before imports")
signal.setitimer(signal.ITIMER_REAL, remaining)
save("run-started.json", {"utc": dt.datetime.now(dt.timezone.utc).isoformat(), "pid": os.getpid(),
                          "process_start_includes_numpy_torch_imports": True, "prior_static_helper_wall_s": prior_static,
                          "alarm_after_s": remaining, "code_sha256": sha(__file__)})


def budget(stage):
    r = resource.getrusage(resource.RUSAGE_SELF)
    rss = r.ru_maxrss if sys.platform == "darwin" else 1024 * r.ru_maxrss
    total = prior_static + time.monotonic() - PROCESS_STARTED
    disk = sum(p.stat().st_size for p in UNIT.rglob("*") if p.is_file())
    data = {"stage": stage, "compute_wall_s_including_imports_and_static": total,
            "process_user_s": r.ru_utime, "process_system_s": r.ru_stime,
            "process_peak_rss_bytes": rss, "new_unit_disk_bytes": disk,
            "wall_cap_s": 600, "rss_cap_bytes": 4 * 1024**3, "disk_cap_bytes": 16 * 1024**2,
            "threads": 6, "utc": dt.datetime.now(dt.timezone.utc).isoformat()}
    (OUT / "budget-progress.json").write_text(json.dumps(data, indent=2) + "\n")
    if total >= 595 or rss >= 4 * 1024**3 or disk >= 16 * 1024**2 or time.time() >= DEADLINE:
        raise RuntimeError("diagnostic resource STOP")
    return data


def event(name, **fields):
    row = {"event": name, "utc": dt.datetime.now(dt.timezone.utc).isoformat(), **fields}
    with open(OUT / "events.jsonl", "a") as f:
        f.write(json.dumps(row, allow_nan=False) + "\n")
    print(json.dumps(row, allow_nan=False), flush=True)


def main():
    import numpy as np
    import torch
    from torch import nn
    from torch.nn import functional as F
    torch.set_num_threads(6)
    torch.set_num_interop_threads(1)
    torch.use_deterministic_algorithms(True)
    budget("imports_completed")
    if sha(PLAN) != PLAN_SHA:
        raise RuntimeError("frozen diagnostic plan identity mismatch")
    authorization = json.loads((UNIT / "root/authorization.json").read_text())
    if authorization["status"] != "USER_AUTHORIZED_SINGLE_COMPLETE_DIAGNOSTIC_UNIT" or authorization["frozen_proposal_sha256"] != PLAN_SHA:
        raise RuntimeError("diagnostic authorization mismatch")
    originals = {name: sha(OLD / name) for name in EXPECTED_HASHES}
    if originals != EXPECTED_HASHES:
        raise RuntimeError("frozen original identity mismatch")
    # Compile only audited pure function/class nodes. No imports/top-level or stage functions.
    tree = ast.parse((OLD / "experiment.py").read_text())
    nodes = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in PURE_NAMES]
    if {node.name for node in nodes} != PURE_NAMES:
        raise RuntimeError("pure-definition allowlist mismatch")
    namespace = {"np": np, "torch": torch, "nn": nn, "F": F, "array": array, "csv": csv, "dt": dt,
                 "gzip": gzip, "hashlib": hashlib, "json": json, "math": math, "Path": Path,
                 "ROOT": OLD, "PLAN_HASH": "c2921f29c37f3d24534d7ef4f88e7df0e25695f5cae581ca958b1a11c2dd089d",
                 "MICRO": 1_000_000, "log": event, "budget": budget}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "audited-pure-definitions-only", "exec"), namespace)
    original_source_path = namespace["source_path"]
    def training_only_source(day):
        if day not in TRAIN:
            raise RuntimeError("forbidden nontraining day")
        return original_source_path(day)
    namespace["source_path"] = training_only_source
    x, y, identities, counts = namespace["sample_days"](TRAIN, True)
    seal = json.loads((OLD / "training-input-seal.json").read_text())
    old_ids = json.loads((OLD / "training-samples.json").read_text())
    stats = json.loads((OLD / "training-statistics.json").read_text())
    fit = json.loads((OLD / "fit-A.json").read_text())
    if len(x) != 22413 or identities != old_ids or namespace["tensor_digest"](x) != seal["raw_transformed_input_sha256"] or namespace["tensor_digest"](y) != seal["target_bp_sha256"]:
        raise RuntimeError("original training input/target/identity mismatch")
    generator, cumulative = np.random.default_rng(20261021), hashlib.sha256()
    for epoch in range(20):
        order = generator.permutation(len(x))
        cumulative.update(order.astype(np.int64).tobytes())
    if cumulative.hexdigest() != fit["epoch_permutations_sha256"]:
        raise RuntimeError("original 20-epoch permutations identity mismatch")
    np.save(OUT / "epoch20-order.npy", order.astype(np.int64), allow_pickle=False)
    np.save(OUT / "training-target-bp.npy", y, allow_pickle=False)
    x = namespace["normalized"](x, stats)
    x[:, :, 4:] = 0
    save("input-identity.json", {"original_hashes": originals, "samples": len(x), "counts": counts,
          "raw_X_sha256": seal["raw_transformed_input_sha256"], "target_sha256": seal["target_bp_sha256"],
          "identity_list_sha256": originals["training-samples.json"], "identities_equal_elementwise": True,
          "normalized_A_input_sha256": namespace["tensor_digest"](x), "cumulative_20_epoch_order_sha256": cumulative.hexdigest(),
          "epoch20_order_sha256": sha(OUT / "epoch20-order.npy"), "batch_count": math.ceil(len(x) / 64), "tail_size": len(x) % 64,
          "pure_definition_names": sorted(PURE_NAMES), "torch_version": torch.__version__, "numpy_version": np.__version__})
    # The only model instance. Safe loading has no unsafe fallback or extra allowlist.
    model = namespace["QuoteRegressor"]()
    weights = torch.load(OLD / "weights-A.pt", map_location="cpu", weights_only=True)
    model.load_state_dict(weights, strict=True)
    del weights
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    model.eval()
    state_digest = namespace["state_digest"]
    initial_state = state_digest(model)
    bn_layers = {name: module for name, module in model.named_modules() if isinstance(module, nn.BatchNorm2d)}
    if len(bn_layers) != 14 or any(module.training for module in model.modules()):
        raise RuntimeError("model eval/frozen BN structure mismatch")
    current = {"mode": None, "batch": -1, "size": None}
    summaries = {mode: {} for mode in ("E", "S")}
    def make_hook(name):
        def hook(module, args):
            value = args[0].detach().to(torch.float64)
            variance, mean = torch.var_mean(value, dim=(0, 2, 3), correction=0)
            n = value.shape[0] * value.shape[2] * value.shape[3]
            if not torch.isfinite(mean).all() or not torch.isfinite(variance).all():
                raise RuntimeError("nonfinite BN preactivation moment")
            m, v = mean.cpu().numpy(), variance.cpu().numpy()
            rows = summaries[current["mode"]]
            if name not in rows:
                rows[name] = {"n": n, "mean": m.copy(), "M2": v * n, "batches": 1}
            else:
                row = rows[name]
                delta = m - row["mean"]
                total = row["n"] + n
                row["M2"] += v * n + delta * delta * row["n"] * n / total
                row["mean"] += delta * n / total
                row["n"] = total
                row["batches"] += 1
            if current["size"] == 13:
                rows[name]["tail13"] = {"mean": m.tolist(), "variance": v.tolist(), "elements_per_channel": n}
            return None
        return hook
    handles = [module.register_forward_pre_hook(make_hook(name)) for name, module in bn_layers.items()]
    all_predictions, metrics = {}, {}
    def moments(pred):
        ym, pm = float(np.mean(y)), float(np.mean(pred))
        vy, vp = float(np.var(y, ddof=0)), float(np.var(pred, ddof=0))
        cov = float(np.mean((pred - pm) * (y - ym)))
        bias2 = (pm - ym)**2
        mse = float(np.mean((pred - y)**2))
        decomposed = vy + vp - 2 * cov + bias2
        if not all(math.isfinite(a) for a in (mse, vy, vp, cov, bias2)) or abs(mse - decomposed) > 1e-8:
            raise RuntimeError("nonfinite or failed moment decomposition")
        return {"mse_bp2": mse, "target_mean_bp": ym, "prediction_mean_bp": pm, "mean_bias_bp": pm - ym,
                "target_variance_bp2": vy, "prediction_variance_bp2": vp, "prediction_target_covariance_bp2": cov,
                "squared_bias_bp2": bias2, "decomposed_mse_bp2": decomposed, "identity_residual_bp2": mse - decomposed}
    for mode in ("E", "S"):
        if mode == "S":
            def batch_stat_forward(module, value):
                return F.batch_norm(value, None, None, module.weight, module.bias, training=True, momentum=0.0, eps=module.eps)
            for module in bn_layers.values():
                module.forward = types.MethodType(batch_stat_forward, module)
        before = state_digest(model)
        if before != initial_state or any(p.requires_grad for p in model.parameters()) or any(m.training for m in model.modules()):
            raise RuntimeError("model state/mode/freeze changed before pass")
        current["mode"] = mode
        prediction = np.empty(len(y), dtype=np.float64)
        event("pass_started", mode=mode, state_sha256=before, budget=budget("pass_" + mode))
        with torch.no_grad():
            for number, (indices, values) in enumerate(namespace["batches"](x, order, False)):
                current.update(batch=number, size=len(indices))
                output = model(values)
                if not torch.isfinite(output).all():
                    raise RuntimeError("nonfinite diagnostic prediction")
                prediction[indices] = output.numpy().astype(np.float64) * stats["target_std"] + stats["target_mean"]
                if state_digest(model) != initial_state:
                    raise RuntimeError("model state changed; do not restore")
                if number % 25 == 0:
                    event("pass_progress", mode=mode, batch=number + 1, total_batches=351, budget=budget("pass_" + mode))
        after = state_digest(model)
        if after != before:
            raise RuntimeError("state digest changed across pass; do not restore")
        metrics[mode] = moments(prediction)
        all_predictions[mode] = prediction
        np.save(OUT / ("predictions-" + mode + "-bp.npy"), prediction, allow_pickle=False)
        save("pass-" + mode + "-seal.json", {"mode": mode, "metrics": metrics[mode], "state_before": before,
                  "state_after": after, "prediction_sha256": sha(OUT / ("predictions-" + mode + "-bp.npy")),
                  "one_complete_pass": True, "samples": len(y), "batches": 351, "budget": budget("sealed_" + mode)})
        if mode == "E" and abs(metrics["E"]["mse_bp2"] - 77.7901551285931) > 0.001:
            raise RuntimeError("E reproduction outside fixed 0.001 bp2; S forbidden")
        event("pass_sealed", mode=mode, metrics=metrics[mode], state_unchanged=True)
    for handle in handles:
        handle.remove()
    hook_output = {}
    for mode, layers in summaries.items():
        hook_output[mode] = {}
        for name, row in layers.items():
            module = bn_layers[name]
            hook_output[mode][name] = {"elements_per_channel": row["n"], "batch_count": row["batches"],
                "pooled_mean": row["mean"].tolist(), "pooled_variance": (row["M2"] / row["n"]).tolist(),
                "saved_running_mean": module.running_mean.numpy().tolist(), "saved_running_var": module.running_var.numpy().tolist(),
                "saved_num_batches_tracked": int(module.num_batches_tracked), "tail13": row["tail13"]}
    save("bn-preactivation-moments.json", hook_output)
    delta = metrics["E"]["mse_bp2"] - metrics["S"]["mse_bp2"]
    baseline, online = 69.34703362319944, 69.21826362518819
    if delta > .001:
        classification = "BN_SOURCE_LOWERS_MSE_AND_S_BELOW_TRAIN_MEAN" if metrics["S"]["mse_bp2"] < baseline else "BN_SOURCE_LOWERS_MSE_BUT_S_NOT_BELOW_TRAIN_MEAN"
    elif delta < -.001:
        classification = "BN_BATCH_SOURCE_INCREASES_MSE"
    else:
        classification = "NO_MODE_EFFECT_ABOVE_NUMERICAL_TOLERANCE"
    after_originals = {name: sha(OLD / name) for name in EXPECTED_HASHES}
    if after_originals != originals:
        raise RuntimeError("original disk evidence changed")
    save("results.json", {"classification": classification, "E": metrics["E"], "S": metrics["S"],
         "delta_E_minus_S_bp2": delta, "online_epoch20_mse_bp2": online,
         "E_minus_online_bp2": metrics["E"]["mse_bp2"] - online,
         "S_minus_online_bp2": metrics["S"]["mse_bp2"] - online,
         "training_mean_baseline_mse_bp2": baseline, "state_before_and_after_all_passes": initial_state,
         "original_hashes_before_and_after": originals, "old_unit_stop_preserved": True,
         "forward_passes": {"E": 1, "S": 1}, "optimizer_steps": 0, "buffer_updates": 0,
         "scope": "same-final-weight training pipeline diagnostic only; S batch statistics are not a causal deployable predictor",
         "budget": budget("completed")})
    event("diagnostic_completed", classification=classification, delta_E_minus_S_bp2=delta)
    files = {p.name: {"bytes": p.stat().st_size, "sha256": sha(p)} for p in OUT.iterdir() if p.is_file() and p.name != "manifest.json"}
    save("manifest.json", {"files": files, "originals_unchanged": originals, "proposal_sha256": PLAN_SHA})
    signal.setitimer(signal.ITIMER_REAL, 0)


if __name__ == "__main__":
    try:
        main()
    except BaseException as exc:
        fail(type(exc).__name__ + ": " + str(exc))
        raise
