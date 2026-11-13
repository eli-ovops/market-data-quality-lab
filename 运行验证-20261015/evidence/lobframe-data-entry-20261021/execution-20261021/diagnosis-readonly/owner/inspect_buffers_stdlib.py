"""Read-only inert pickle metadata inspection; no torch/pickle.load/model calls."""
import collections
import datetime
import hashlib
import json
import math
from pathlib import Path
import pickletools
import resource
import statistics
import struct
import sys
import time
import zipfile

OUT = Path(__file__).resolve().parent
ROOT = OUT.parent.parent
START = time.perf_counter()
resource.setrlimit(resource.RLIMIT_CPU, (55, 55))
MARK = object()


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def inert_metadata(data):
    """Tiny allowlisted stack interpreter: REDUCE/GLOBAL/BUILD are NEVER called.

    Only the known OrderedDict and tensor metadata patterns are represented.
    Unexpected types/opcodes abort, rather than importing/deserializing objects.
    """
    stack, memo = [], {}
    attributes = []
    counts = collections.Counter()
    globals_seen = set()

    def pop_mark():
        i = len(stack) - 1
        while i >= 0 and stack[i] is not MARK:
            i -= 1
        if i < 0:
            raise ValueError("missing pickle MARK")
        items = stack[i + 1:]
        del stack[i:]
        return items

    for op, arg, position in pickletools.genops(data):
        name = op.name
        counts[name] += 1
        if name == "PROTO":
            if arg != 2:
                raise ValueError("unsupported protocol")
        elif name == "GLOBAL":
            if arg not in {"collections OrderedDict", "torch FloatStorage", "torch LongStorage", "torch._utils _rebuild_tensor_v2"}:
                raise ValueError("unrecognized inert GLOBAL: " + arg)
            globals_seen.add(arg)
            stack.append(("GLOBAL_TOKEN", arg))
        elif name in {"BINPUT", "LONG_BINPUT"}:
            memo[arg] = stack[-1]
        elif name in {"BINGET", "LONG_BINGET"}:
            stack.append(memo[arg])
        elif name == "MARK":
            stack.append(MARK)
        elif name in {"BINUNICODE", "BININT1", "BININT2", "BININT", "LONG1"}:
            stack.append(arg)
        elif name == "NEWFALSE":
            stack.append(False)
        elif name == "NEWTRUE":
            stack.append(True)
        elif name == "NONE":
            stack.append(None)
        elif name == "EMPTY_TUPLE":
            stack.append(())
        elif name == "EMPTY_DICT":
            stack.append({})
        elif name == "TUPLE":
            stack.append(tuple(pop_mark()))
        elif name in {"TUPLE1", "TUPLE2", "TUPLE3"}:
            n = int(name[-1])
            values = tuple(stack[-n:])
            del stack[-n:]
            stack.append(values)
        elif name == "BINPERSID":
            storage = stack.pop()
            if not isinstance(storage, tuple) or len(storage) != 5 or storage[0] != "storage":
                raise ValueError("unexpected persistent storage identifier")
            _, dtype, key, location, length = storage
            if dtype not in {("GLOBAL_TOKEN", "torch FloatStorage"), ("GLOBAL_TOKEN", "torch LongStorage")} or location != "cpu":
                raise ValueError("unsupported storage dtype/location")
            stack.append({"storage_type": dtype[1], "storage_key": key, "location": location, "storage_length": length})
        elif name == "REDUCE":
            args, function_token = stack.pop(), stack.pop()
            if function_token == ("GLOBAL_TOKEN", "collections OrderedDict") and args == ():
                stack.append({})
            elif function_token == ("GLOBAL_TOKEN", "torch._utils _rebuild_tensor_v2"):
                if len(args) != 6 or not isinstance(args[0], dict):
                    raise ValueError("unexpected tensor metadata arguments")
                storage, offset, shape, stride, requires_grad, hooks = args
                stack.append({"tensor_metadata": True, **storage, "offset": offset, "shape": shape,
                              "stride": stride, "requires_grad": requires_grad})
            else:
                raise ValueError("unsupported symbolic REDUCE; callable never executed")
        elif name == "SETITEMS":
            items = pop_mark()
            if len(items) % 2 or not isinstance(stack[-1], dict):
                raise ValueError("invalid SETITEMS")
            stack[-1].update(zip(items[::2], items[1::2]))
        elif name == "SETITEM":
            value, key = stack.pop(), stack.pop()
            if not isinstance(stack[-1], dict):
                raise ValueError("invalid SETITEM")
            stack[-1][key] = value
        elif name == "BUILD":
            # torch state_dict OrderedDict _metadata; record inert attributes only.
            state = stack.pop()
            if not isinstance(state, dict) or not isinstance(stack[-1], dict):
                raise ValueError("unexpected inert BUILD")
            attributes.append(state)
        elif name == "STOP":
            if len(stack) != 1 or not isinstance(stack[0], dict):
                raise ValueError("unexpected final pickle stack")
            return stack[0], attributes, dict(counts), sorted(globals_seen)
        else:
            raise ValueError(f"unsupported opcode {name} at {position}; stop without fallback")
    raise ValueError("pickle STOP missing")


def expected_shapes():
    result = {}
    units = []
    for block in range(3):
        units += [(f"spatial.{block}.0", 1 if block == 0 else 32, 32, (1, 10 if block == 2 else 2)),
                  (f"spatial.{block}.1", 32, 32, (4, 1)), (f"spatial.{block}.2", 32, 32, (4, 1))]
    units += [("branches.0.0", 32, 64, (1, 1)), ("branches.0.1", 64, 64, (3, 1)),
              ("branches.1.0", 32, 64, (1, 1)), ("branches.1.1", 64, 64, (5, 1)),
              ("branches.2.1", 32, 64, (1, 1))]
    for prefix, incoming, outgoing, kernel in units:
        result[prefix + ".conv.weight"] = (outgoing, incoming, *kernel)
        result[prefix + ".conv.bias"] = (outgoing,)
        for name in ("weight", "bias", "running_mean", "running_var"):
            result[prefix + ".norm." + name] = (outgoing,)
        result[prefix + ".norm.num_batches_tracked"] = ()
    result.update({"sequence.weight_ih_l0": (256, 192), "sequence.weight_hh_l0": (256, 64),
                   "sequence.bias_ih_l0": (256,), "sequence.bias_hh_l0": (256,),
                   "output.weight": (1, 64), "output.bias": (1,)})
    return result


def summarize(values):
    finite = [v for v in values if math.isfinite(v)]
    return {"count": len(values), "nonfinite": len(values) - len(finite),
            "nan": sum(math.isnan(v) for v in values), "positive_inf": sum(v == math.inf for v in values),
            "negative_inf": sum(v == -math.inf for v in values), "zero": sum(v == 0 for v in finite),
            "negative": sum(v < 0 for v in finite), "minimum": min(finite) if finite else None,
            "maximum": max(finite) if finite else None,
            "mean": statistics.fmean(finite) if finite else None,
            "population_std": statistics.pstdev(finite) if len(finite) > 1 else 0 if finite else None}


def main():
    evidence_names = ["experiment.py", "weights-A.pt", "fit-A.json", "training-statistics.json", "execution-events.jsonl",
                      "training-input-seal.json", "training-input-seal-before-gatefix.json", "prefit-gate-amendment.json",
                      "technical-stop.json", "selfcheck.json", "terminal-receipt.json"]
    before = {name: sha(ROOT / name) for name in evidence_names}
    assert before["experiment.py"] == "148a44f30da8966d7fa076ea7f152ed3396f936be0a8d800c810f388bdefdf05"
    assert before["weights-A.pt"] == "fa200c539704f1e78d69c47519980947c589dba1d5e5ea72a6a40cf89e5aa637"
    fit = json.loads((ROOT / "fit-A.json").read_text())
    stats = json.loads((ROOT / "training-statistics.json").read_text())
    events = [json.loads(s) for s in (ROOT / "execution-events.jsonl").read_text().splitlines()]
    seal = json.loads((ROOT / "training-input-seal.json").read_text())
    old_seal = json.loads((ROOT / "training-input-seal-before-gatefix.json").read_text())
    amendment = json.loads((ROOT / "prefit-gate-amendment.json").read_text())
    assert seal["implementation_sha256"] == before["experiment.py"]
    assert seal["statistics_sha256"] == before["training-statistics.json"]
    for key in ("raw_transformed_input_sha256", "target_bp_sha256", "statistics_sha256", "samples_sha256"):
        assert seal[key] == old_seal[key]
    assert amendment["original_seal_sha256"] == before["training-input-seal-before-gatefix.json"]
    assert fit["weight_sha256"] == before["weights-A.pt"]
    epochs = [e for e in events if e["event"] == "epoch"]
    assert [e["epoch"] for e in epochs] == list(range(1, 21))
    assert all(e["model"] == "A" for e in epochs)
    count = stats["training_samples"]
    batches = (count + 63) // 64
    expected_bn_count = batches * 20
    tensors, bn_rows, storage_members = {}, [], []
    with zipfile.ZipFile(ROOT / "weights-A.pt") as z:
        if any(i.file_size > 1024 * 1024 for i in z.infolist()) or sum(i.file_size for i in z.infolist()) > 5 * 1024**2:
            raise ValueError("archive size bound exceeded")
        assert z.testzip() is None
        names = z.namelist()
        prefix = next(n[:-len("data.pkl")] for n in names if n.endswith("/data.pkl"))
        assert z.read(prefix + "byteorder") == b"little"
        metadata, attributes, opcodes, globals_seen = inert_metadata(z.read(prefix + "data.pkl"))
        expected = expected_shapes()
        assert set(metadata) == set(expected)
        decoded = {}
        for name, item in metadata.items():
            assert item["tensor_metadata"] and tuple(item["shape"]) == expected[name]
            dims = item["shape"]
            contiguous = []
            stride = 1
            for d in reversed(dims):
                contiguous.append(stride)
                stride *= d
            assert tuple(reversed(contiguous)) == tuple(item["stride"])
            assert item["offset"] == 0 and stride == item["storage_length"]
            member = prefix + "data/" + item["storage_key"]
            body = z.read(member)
            code = "f" if item["storage_type"] == "torch FloatStorage" else "q"
            width = 4 if code == "f" else 8
            assert len(body) == width * item["storage_length"]
            values = [v[0] for v in struct.iter_unpack("<" + code, body)]
            decoded[name] = values
            tensors[name] = {"shape": list(dims), "stride": list(item["stride"]), "dtype": item["storage_type"],
                             "zip_member": member, "buffer_sha256": hashlib.sha256(body).hexdigest(), **summarize(values)}
            storage_members.append(member)
        for name in metadata:
            if name.endswith(".running_var"):
                layer = name[:-len(".running_var")]
                var = decoded[name]
                gamma = decoded[layer + ".weight"]
                beta = decoded[layer + ".bias"]
                mean = decoded[layer + ".running_mean"]
                tracked = decoded[layer + ".num_batches_tracked"]
                gain = [g / math.sqrt(v + 1e-5) if v + 1e-5 > 0 else math.nan for g, v in zip(gamma, var)]
                bn_rows.append({"layer": layer, "channels": len(var), "num_batches_tracked": tracked,
                                "expected_batches": expected_bn_count, "count_matches": tracked == [expected_bn_count],
                                "variance": summarize(var), "variance_below_eps": sum(v < 1e-5 for v in var),
                                "variance_below_1e_8": sum(v < 1e-8 for v in var),
                                "running_mean": summarize(mean), "gamma": summarize(gamma), "beta": summarize(beta),
                                "eval_affine_gain": summarize(gain),
                                "buffers": {"running_var": var, "running_mean": mean, "gamma": gamma, "beta": beta}})
        zip_summary = {"member_count": len(names), "uncompressed_bytes": sum(i.file_size for i in z.infolist()),
                       "crc_all_members_pass": True, "byteorder": "little", "pickle_opcodes": opcodes,
                       "inert_global_tokens": globals_seen, "inert_metadata_attributes": attributes,
                       "storage_members": storage_members}
    assert len(bn_rows) == 14
    after = {name: sha(ROOT / name) for name in evidence_names}
    assert before == after
    report = {"utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "method": "zipfile + pickletools.genops + allowlisted inert stack metadata parser + little-endian struct buffers",
              "pickle_callables_executed": 0, "torch_imported": "torch" in sys.modules,
              "model_instantiations": 0, "forwards": 0, "backwards": 0, "test_data_reads": 0,
              "evidence_hashes_before_and_after_unchanged": before,
              "training": {"samples": count, "batch_size": 64, "batches_per_epoch": batches,
                           "last_batch_samples": count % 64, "epochs": len(epochs), "expected_bn_updates": expected_bn_count,
                           "batch_mse_standardized_by_epoch": [e["batch_loss_standardized"] for e in epochs],
                           "final_train_eval_mse_bp2": fit["train_eval_mse_bp2"], "target_mean": stats["target_mean"],
                           "target_std": stats["target_std"], "target_std_squared": stats["target_std"]**2,
                           "mean_baseline_mse_bp2": fit["train_mean_baseline_mse_bp2"]},
              "zip": zip_summary, "tensor_count": len(tensors), "tensors": tensors,
              "all_tensor_values_finite": all(t["nonfinite"] == 0 for t in tensors.values()),
              "bn_layers": bn_rows, "all_bn_counts_match": all(b["count_matches"] for b in bn_rows),
              "all_shapes_and_contiguous_storage_lengths_match_static_definition": True,
              "resource": {"single_thread_standard_library_only": True, "wall_s": time.perf_counter() - START,
                           "process_user_s": resource.getrusage(resource.RUSAGE_SELF).ru_utime,
                           "process_system_s": resource.getrusage(resource.RUSAGE_SELF).ru_stime,
                           "cpu_soft_hard_limit_s": [55, 55], "python_version": sys.version}}
    (OUT / "buffer-inspection.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
    compact = {"tensor_count": len(tensors), "finite": report["all_tensor_values_finite"], "bn_counts_match": report["all_bn_counts_match"],
               "bn": [{k: row[k] for k in ("layer", "channels", "num_batches_tracked", "variance_below_eps", "variance_below_1e_8")} |
                      {"min_var": row["variance"]["minimum"], "max_var": row["variance"]["maximum"], "max_abs_gain": max(abs(x) for x in [row["eval_affine_gain"]["minimum"], row["eval_affine_gain"]["maximum"]])} for row in bn_rows],
               "resource": report["resource"], "report_sha256": sha(OUT / "buffer-inspection.json")}
    print(json.dumps(compact, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
