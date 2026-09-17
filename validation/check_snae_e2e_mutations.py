"""Reject corrupted end-to-end outcomes in a disposable completed oracle container.

Commit each mutation so rejection checks the outcome, not just a dirty tree.
Restore the original commit and file after each check. Never run on a real project.
"""

import json
import os
import subprocess
from contextlib import contextmanager
from pathlib import Path

import yaml

ROOT = Path("/root/snae")
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


@contextmanager
def changed(relative, content):
    path = ROOT / relative
    head = git("rev-parse", "HEAD")
    assert not git("status", "--porcelain")
    link = path.readlink() if path.is_symlink() else None
    original = path.read_bytes() if path.exists() else None
    mode = path.stat().st_mode if path.exists() else None
    ignored = (
        subprocess.run(
            ["git", "check-ignore", "-q", relative], cwd=ROOT, check=False
        ).returncode
        == 0
    )
    try:
        if path.exists() or path.is_symlink():
            path.unlink()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        if not ignored:
            git("add", "--", relative)
            git("commit", "-qm", "Validation: inject incorrect outcome")
        yield
    finally:
        git("reset", "--hard", head)
        # Let Git/annex restore tracked objects and their index representation.
        annexed = (
            subprocess.run(
                ["git", "annex", "lookupkey", "--", relative],
                cwd=ROOT,
                capture_output=True,
                check=False,
            ).returncode
            == 0
        )
        if annexed:
            # An unlocked checkout can briefly contain an annex pointer after
            # reset. Explicitly populate it before checking the restored bytes.
            git("annex", "get", "--", relative)
            git("add", "--", relative)
            git("annex", "restage")
        if ignored:
            if path.exists() or path.is_symlink():
                path.unlink()
            if link is not None:
                path.symlink_to(link)
            elif original is not None:
                path.write_bytes(original)
                path.chmod(mode)
        if original is not None:
            assert path.read_bytes() == original
        git("diff", "--quiet")
        assert not git("status", "--porcelain")


def rejected(name, test, expected):
    result = subprocess.run(
        ["python3", "-m", "pytest", "-p", "no:cacheprovider", "-q", f"/tests/{test}"],
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    assert result.returncode == 1 and expected in result.stdout, (
        f"{name}: expected a relevant assertion failure\n{result.stdout}\n{result.stderr}"
    )
    assert "ERROR collecting" not in result.stdout
    print(f"REJECTED: {name}", flush=True)


record = json.loads((ROOT / ".lightcone/estimates.json").read_text())
record["estimates"][0]["evidence"] = []
with changed(".lightcone/estimates.json", json.dumps(record).encode()):
    rejected(
        "resource estimate without evidence",
        "test_estimation.py::test_evidence_is_auditable_and_matches_astra",
        'assert estimate["evidence"]',
    )

spec = yaml.safe_load((ROOT / "astra.yaml").read_text())
spec["outputs"][0]["recipe"]["resources"]["gpus"] = 1
with changed("astra.yaml", yaml.safe_dump(spec, sort_keys=False).encode()):
    rejected(
        "unsupported GPU request",
        "test_estimation.py::test_every_recipe_has_only_supported_resources",
        "RESOURCE_KEYS",
    )

with changed("results/baseline/best_fit.zip", b"invalid archive"):
    rejected(
        "corrupt fit artifact",
        "test_sync.py::test_best_fit_artifacts_exist",
        "BadZipFile",
    )

manifest_path = "results/baseline/.best_fit.manifest.json"
manifest = json.loads((ROOT / manifest_path).read_text())
manifest["data_version"] = "sha256:" + "0" * 64
with changed(manifest_path, json.dumps(manifest).encode()):
    rejected(
        "forged output provenance",
        "test_sync.py::test_manifest_records_local_lightcone_provenance",
        "data_version",
    )

with changed("results/baseline/residuals.png", b"unrequested output"):
    rejected(
        "unrequested figure materialized",
        "test_sync.py::test_no_async_record_or_downstream_output_was_created",
        "residuals.png",
    )

plan = json.loads((ROOT / "execution-plan.json").read_text())
plan["decision"] = "run-locally"
with changed("execution-plan.json", json.dumps(plan).encode()):
    rejected(
        "oversized work assigned to the local host",
        "test_classification.py::test_plan_moves_work_instead_of_claiming_local_async",
        "move-to-supported-environment",
    )

spec = yaml.safe_load((ROOT / "astra.yaml").read_text())
spec["outputs"][-1]["recipe"]["resources"]["cpus"] = 1
with changed("astra.yaml", yaml.safe_dump(spec, sort_keys=False).encode()):
    rejected(
        "production resource request silently reduced",
        "test_classification.py::test_astra_is_valid_and_demand_is_complete",
        "Scientific methods or the production request changed",
    )

print("All 7 corrupted end-to-end outcomes were rejected.")
