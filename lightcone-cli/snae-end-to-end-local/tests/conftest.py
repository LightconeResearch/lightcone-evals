"""Trusted references and current Lightcone contracts shared by all dimensions."""

import json
import os
import subprocess
from pathlib import Path

import pytest
import yaml

PROJECT = Path(os.environ.get("TASK_PROJECT_ROOT", "/root/snae"))
REFERENCE = Path("/opt/snae-e2e-reference")
FORMATS = {
    "best_fit": "zip",
    "hubble_diagram": "png",
    "residuals": "png",
    "bootstrap_intervals": "zip",
}


def git(*args):
    result = subprocess.run(
        ["git", *args],
        cwd=PROJECT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def validate_astra():
    # Use the CLI's root-owned ASTRA dependency, not an agent-writable uvx cache.
    result = subprocess.run(
        [
            "/opt/uv-tools/lightcone-cli/bin/python",
            "-c",
            (
                "from pathlib import Path; import sys; "
                "from astra.validation import validate_analysis_file, validate_analysis_schema, validate_universe_file; "
                "p=Path(sys.argv[1]); errors=[*validate_analysis_schema(p), *validate_analysis_file(p)]; "
                "errors.extend(validate_universe_file(p.parent/'universes/baseline.yaml', p)); "
                "assert not errors, errors"
            ),
            str(PROJECT / "astra.yaml"),
        ],
        cwd=PROJECT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def assert_unrequested_outputs_absent():
    for name in ("hubble_diagram", "residuals", "bootstrap_intervals"):
        for path in (
            PROJECT / f"results/baseline/{name}.{FORMATS[name]}",
            PROJECT / f"results/baseline/.{name}.manifest.json",
            PROJECT / f"results/baseline/{name}",
        ):
            assert not path.exists() and not path.is_symlink(), str(path)


@pytest.fixture(scope="module", autouse=True)
def preserved_scientific_contract():
    reference = REFERENCE / "project"
    original = yaml.safe_load((reference / "astra.yaml").read_text())
    actual = yaml.safe_load((PROJECT / "astra.yaml").read_text())
    for output in actual["outputs"]:
        if output["id"] != "bootstrap_intervals":
            output["recipe"].pop("resources", None)
    assert actual == original, "Scientific methods or the production request changed"
    for path in reference.rglob("*"):
        if path.is_file() and path.name != "astra.yaml":
            assert (
                PROJECT / path.relative_to(reference)
            ).read_bytes() == path.read_bytes(), str(path)
    state = json.loads((REFERENCE / "state.json").read_text())
    git("merge-base", "--is-ancestor", state["head"], "HEAD")
    assert not git("status", "--porcelain"), (
        "The final project must be committed and clean"
    )
