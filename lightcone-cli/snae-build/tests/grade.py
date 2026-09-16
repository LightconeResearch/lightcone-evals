"""Five outcome dimensions; no agent reporting protocol or manual checkpoints."""

import json
import os
import subprocess
from pathlib import Path

LOGS = Path(os.environ.get("LOGS_DIR", "/logs/verifier"))
TESTS = Path(__file__).with_name("test_outcomes.py")
DIMENSIONS = {
    "targeted_execution": (20, "test_targeted_execution"),
    "incremental_execution": (20, "test_incremental_execution"),
    "failure_recovery": (20, "test_failure_recovery"),
    "clone_reproduction": (20, "test_clone_reproduction"),
    "publication_provenance": (20, "test_publication_provenance"),
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
for name in (
    "new-analysis",
    "updated-analysis",
    "interrupted-analysis",
    "reproduced-analysis",
):
    root = Path("/root/snae-natural") / name
    with (LOGS / f"{name}-history.txt").open("w") as log:
        subprocess.run(
            ["git", "-C", str(root), "log", "--all", "--decorate", "--oneline"],
            stdout=log,
            stderr=subprocess.STDOUT,
            check=False,
        )
print(json.dumps(reward))
