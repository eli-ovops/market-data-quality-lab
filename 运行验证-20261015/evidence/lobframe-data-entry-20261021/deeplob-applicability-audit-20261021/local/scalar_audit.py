"""Standard-library descriptive scalars from sealed aggregate moments only."""
import time
START = time.process_time()
import datetime
import hashlib
import json
import math
from pathlib import Path

OUT = Path(__file__).resolve().parent
BASE = OUT.parent.parent
SOURCE = BASE / "diagnosis-forward-once-20261021/owner/results.json"
CODE = BASE / "execution-20261021/experiment.py"
STOP = BASE / "execution-20261021/technical-stop.json"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


before = {"results": sha(SOURCE), "frozen_code": sha(CODE), "old_stop": sha(STOP)}
assert before["results"] == "79f8c8516d4d8bfc0ef3d591c3a5208c8fe0fc41eaeffdb2e28cc9c6890a8c10"
assert before["frozen_code"] == "148a44f30da8966d7fa076ea7f152ed3396f936be0a8d800c810f388bdefdf05"
assert before["old_stop"] == "6f37b1f1de6441500181531e4ac9acf570145a35cfc9cea9dfdcfcd90317bc1e"
data = json.loads(SOURCE.read_text())
rows = {}
for mode in ("E", "S"):
    m = data[mode]
    rho = m["prediction_target_covariance_bp2"] / math.sqrt(m["prediction_variance_bp2"] * m["target_variance_bp2"])
    # This is an existing moment-identity component, NOT a new shifted prediction.
    dispersion_component = m["prediction_variance_bp2"] - 2 * m["prediction_target_covariance_bp2"]
    excess = m["mse_bp2"] - m["target_variance_bp2"]
    assert abs(excess - dispersion_component - m["squared_bias_bp2"]) < 1e-8
    rows[mode] = {"pearson_correlation_descriptive": rho,
                  "mse_bp2": m["mse_bp2"], "mean_bias_bp": m["mean_bias_bp"],
                  "bias_squared_bp2": m["squared_bias_bp2"],
                  "prediction_variance_minus_2cov_bp2": dispersion_component,
                  "dispersion_component_fraction_of_target_variance": dispersion_component / m["target_variance_bp2"],
                  "mse_excess_above_training_mean_bp2": excess,
                  "moment_identity_residual_bp2": excess - dispersion_component - m["squared_bias_bp2"]}
after = {"results": sha(SOURCE), "frozen_code": sha(CODE), "old_stop": sha(STOP)}
assert before == after
cpu = time.process_time() - START
assert cpu < 1.0
report = {"utc": datetime.datetime.now(datetime.timezone.utc).isoformat(), "input_original_hashes_unchanged": before,
          "rows": rows, "method": "two sealed aggregate moment records; Pearson and MSE identity components only",
          "new_prediction_vectors": 0, "linear_calibrations_or_bias_fits": 0, "model_imports_or_loads": 0,
          "forward_passes": 0, "csv_reads": 0, "new_test_performance_reads": 0,
          "activation_moment_reads": 0, "new_return_calculations": 0,
          "scalar_helper_cpu_s_including_imports": cpu,
          "scope": "descriptive training-set association, not accuracy, causal deployment, test evidence or economic utility",
          "actual_model": "UNKNOWN", "actual_effort": "UNKNOWN"}
(OUT / "scalars.json").write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n")
print(json.dumps(report, ensure_ascii=False, allow_nan=False))
