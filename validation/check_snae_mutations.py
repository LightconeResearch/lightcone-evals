"""Reject corrupted outcomes for either paired SNAE task in a completed oracle container."""

import subprocess
from contextlib import contextmanager
from pathlib import Path

ROOT = Path("/root/snae-natural")


@contextmanager
def changed(path, content):
    original = path.read_bytes() if path.exists() else None
    try:
        path.write_bytes(content)
        yield
    finally:
        if original is None:
            path.unlink()
        else:
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
            f"/tests/test_outcomes.py::{test}",
        ],
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    assert result.returncode == 1, (
        f"{name}: expected assertion failure, got {result.returncode}\n{result.stdout}\n{result.stderr}"
    )
    print(f"REJECTED: {name}")


with changed(
    ROOT / "new-analysis/results/baseline/residuals.png", b"unrequested product"
):
    rejected("unrequested output created", "test_targeted_execution")
path = ROOT / "updated-analysis/universes/baseline.yaml"
with changed(
    path,
    path.read_bytes().replace(b"error_model: stat_only", b"error_model: stat_and_sys"),
):
    rejected("requested uncertainty treatment undone", "test_incremental_execution")
path = ROOT / "interrupted-analysis/data/SCPUnion2.1_mu_vs_z.txt"
with changed(
    path,
    Path("/opt/snae-natural-reference/seed/data/SCPUnion2.1_mu_vs_z.txt").read_bytes(),
):
    rejected("corrected measurement discarded", "test_failure_recovery")
with changed(
    ROOT / "reproduced-analysis/results/baseline/best_fit.json", b'{"wrong": true}\n'
):
    rejected("reproduced bytes corrupted", "test_clone_reproduction")
with changed(
    ROOT / "updated-analysis/ro-crate-metadata.json",
    b'{"@context": "x", "@graph": []}\n',
):
    rejected("empty publication metadata", "test_publication_provenance")
with changed(ROOT / "new-analysis/scripts/fit.py", b'print("placeholder output")\n'):
    rejected("scientific recipe replaced", "test_targeted_execution")
print("All 6 corrupted paired-task outcomes were rejected.")
