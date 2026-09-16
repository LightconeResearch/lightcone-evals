"""Run inside a completed oracle container: each corrupted result must lose credit.

Mount this directory at /validation and the task tests at /tests. No model calls.
Every mutation is restored before moving on; fails if a verifier accepts it.
"""

import json
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

sys.path.insert(0, "/tests")
from test_execution import load_report

ROOT = Path("/root/snae-build")
REPORTS = Path("/root/snae-build-reports")
CLONE = Path("/root/snae-reproduced")


@contextmanager
def changed(path, content):
    original = path.read_bytes()
    try:
        path.write_bytes(content)
        yield
    finally:
        path.write_bytes(original)


def rejected(name, test):
    result = subprocess.run(
        [
            "python3",
            "-m",
            "pytest",
            "-p",
            "no:cacheprovider",
            "-q",
            f"/tests/test_execution.py::{test}",
        ],
        capture_output=True,
        text=True,
        timeout=100,
        check=False,
    )
    assert result.returncode == 1, (
        f"{name}: expected assertion failure, got {result.returncode}\n{result.stdout}\n{result.stderr}"
    )
    print(f"REJECTED: {name}")


cases = [
    (
        "unrequested output ran",
        "targeted",
        {
            "made": [
                "baseline/best_fit",
                "baseline/hubble_diagram",
                "baseline/residuals",
            ]
        },
        "test_targeted_execution",
    ),
    (
        "no-op reran a recipe",
        "repeat",
        {"made": ["baseline/best_fit"]},
        "test_idempotent_repeat",
    ),
    (
        "unrelated branch rebuilt",
        "decision",
        {
            "made": [
                "baseline/best_fit",
                "baseline/hubble_diagram",
                "baseline/residuals",
                "baseline/catalog_summary",
            ]
        },
        "test_decision_and_input_invalidation",
    ),
    (
        "false success after failure",
        "failed",
        {"ok": True},
        "test_failure_rollback_and_recovery",
    ),
]
for name, stage, patch, test in cases:
    path = REPORTS / f"{stage}.json"
    payload = load_report(path)
    with changed(path, json.dumps({**payload, **patch}).encode()):
        rejected(name, test)
with changed(REPORTS / "failed.exitcode", b"0\n"):
    rejected("missing failure exit status", "test_failure_rollback_and_recovery")
with changed(CLONE / "results/baseline/best_fit.json", b'{"wrong": true}\n'):
    rejected("clone output corruption", "test_fresh_clone_reproduces")
with changed(ROOT / "ro-crate-metadata.json", b'{"@context": "x", "@graph": []}\n'):
    rejected("empty publication metadata", "test_publication_and_final_state")
# Refuse a forged success report even if its JSON still looks plausible.
old = subprocess.check_output(
    ["git", "-C", str(ROOT), "rev-parse", "eval/repeat"], text=True
).strip()
try:
    subprocess.run(
        ["git", "-C", str(ROOT), "tag", "-f", "eval/repeat", "eval/decision"],
        check=True,
        capture_output=True,
    )
    rejected("no-op checkpoint actually advanced", "test_idempotent_repeat")
finally:
    subprocess.run(
        ["git", "-C", str(ROOT), "tag", "-f", "eval/repeat", old],
        check=True,
        capture_output=True,
    )
print("All 8 corrupted outcomes were rejected.")
