"""Seven separately scored execution dimensions, all deterministic."""

import json
import os
import shutil
import subprocess
from pathlib import Path

LOGS = Path(os.environ.get("LOGS_DIR", "/logs/verifier"))
TESTS = Path(__file__).with_name("test_execution.py")
DIMENSIONS = {
    "targeted_execution": (15, "test_targeted_execution"),
    "full_execution": (15, "test_full_execution_and_preserved_contract"),
    "idempotent_repeat": (10, "test_idempotent_repeat"),
    "selective_invalidation": (20, "test_decision_and_input_invalidation"),
    "failure_recovery": (15, "test_failure_rollback_and_recovery"),
    "clone_reproduction": (15, "test_fresh_clone_reproduces"),
    "publication_provenance": (10, "test_publication_and_final_state"),
}
LOGS.mkdir(parents=True, exist_ok=True)
subprocess.run(
    ["git", "config", "--global", "--add", "safe.directory", "*"], check=True
)
reward = {"reward": 0.0}
points = 0
for name, (weight, test) in DIMENSIONS.items():
    with (LOGS / f"{name}.txt").open("w") as log:
        try:
            code = subprocess.run(
                [
                    "python3",
                    "-m",
                    "pytest",
                    "-p",
                    "no:cacheprovider",
                    f"{TESTS}::{test}",
                    "-vv",
                    "--tb=short",
                ],
                stdout=log,
                stderr=subprocess.STDOUT,
                timeout=70,
                check=False,
            ).returncode
        except subprocess.TimeoutExpired:
            code = 124
    print((LOGS / f"{name}.txt").read_text())
    reward[name] = float(code == 0)
    if code == 0:
        points += weight
reward["reward"] = points / 100
(LOGS / "reward.txt").write_text(f"{points / 100:.2f}\n")
(LOGS / "reward.json").write_text(json.dumps(reward, indent=2) + "\n")
reports = Path(os.environ.get("REPORTS", "/root/snae-build-reports"))
if reports.is_dir():
    shutil.copytree(reports, LOGS / "execution-reports", dirs_exist_ok=True)
root = Path(os.environ.get("PROJECT", "/root/snae-build"))
with (LOGS / "git-history.txt").open("w") as log:
    subprocess.run(
        ["git", "-C", str(root), "log", "--all", "--decorate", "--oneline"],
        stdout=log,
        stderr=subprocess.STDOUT,
        check=False,
    )
print(json.dumps(reward))
