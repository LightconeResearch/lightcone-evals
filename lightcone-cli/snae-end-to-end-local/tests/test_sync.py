from __future__ import annotations

import hashlib
import io
import json
import subprocess
from zipfile import ZipFile

import numpy as np
from conftest import PROJECT, REFERENCE, assert_unrequested_outputs_absent, git

OUTPUT = PROJECT / "results/baseline/best_fit.zip"
MANIFEST = PROJECT / "results/baseline/.best_fit.manifest.json"


def fit_result():
    with ZipFile(OUTPUT) as archive:
        return json.loads(archive.read("best_fit.json"))


def test_best_fit_artifacts_exist() -> None:
    assert OUTPUT.is_file() and MANIFEST.is_file()
    with ZipFile(OUTPUT) as archive:
        assert sorted(archive.namelist()) == ["best_fit.json", "fitted_model.csv"]
        assert archive.testzip() is None


def test_fit_is_physically_and_internally_reasonable() -> None:
    fit = fit_result()
    assert 50.0 < fit["H0_km_s_Mpc"] < 90.0
    assert 0.0 < fit["Omega_L"] < 1.0
    assert abs(fit["Omega_m"] + fit["Omega_L"] - 1.0) < 1e-10
    assert fit["degrees_of_freedom"] == fit["n_supernovae"] - 2
    assert 0.0 < fit["reduced_chi_squared"] < 5.0
    assert fit["optimizer"] == "nelder_mead"
    assert fit["error_model"] == "stat_and_sys"
    assert fit["redshift_cut"] == "z_min_001"


def test_fit_uses_exactly_the_selected_union21_rows() -> None:
    raw = np.loadtxt(
        PROJECT / "data/SCPUnion2.1_mu_vs_z.txt", comments="#", usecols=(1, 2)
    )
    selected = raw[raw[:, 0] > 0.01]
    fit = fit_result()
    with ZipFile(OUTPUT) as archive:
        model = np.loadtxt(
            io.BytesIO(archive.read("fitted_model.csv")), delimiter=",", skiprows=1
        )
    assert fit["n_supernovae"] == len(selected)
    assert model.shape == (len(selected), 5)
    assert np.all(np.isfinite(model))
    np.testing.assert_allclose(model[:, :2], selected)
    np.testing.assert_allclose(model[:, 3], model[:, 1] - model[:, 2], atol=1e-12)
    assert np.isclose(np.sum((model[:, 3] / model[:, 4]) ** 2), fit["chi_squared"])


def test_manifest_records_local_lightcone_provenance() -> None:
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["output_id"] == "best_fit"
    assert manifest["universe_id"] == "baseline"
    for key in (
        "lc_version",
        "uv_version",
        "env_version",
        "definition_version",
        "recipe",
    ):
        assert manifest[key]
    assert manifest["image"] is None
    assert manifest["hermeticity"]["fs"] == "declared"
    assert manifest["hermeticity"]["mechanism"] == "landlock"
    assert manifest["decisions"] == {
        "optimizer": "nelder_mead",
        "error_model": "stat_and_sys",
        "redshift_cut": "z_min_001",
    }
    assert (
        manifest["data_version"]
        == "sha256:" + hashlib.sha256(OUTPUT.read_bytes()).hexdigest()
    )
    assert manifest["input_versions"] == {
        "union21": "sha256:"
        + hashlib.sha256(
            (PROJECT / "data/SCPUnion2.1_mu_vs_z.txt").read_bytes()
        ).hexdigest()
    }
    recorded = git("log", "-1", "--format=%H", "--", str(MANIFEST.relative_to(PROJECT)))
    assert "[DATALAD RUNCMD]" in git("show", "-s", "--format=%B", recorded)
    git("merge-base", "--is-ancestor", manifest["git_sha"], recorded)
    assert (
        json.loads(git("show", "HEAD:results/baseline/.best_fit.manifest.json"))
        == manifest
    )
    state = json.loads((REFERENCE / "state.json").read_text())
    history = git("log", "--format=%B", f"{state['head']}..HEAD")
    assert history.count("[DATALAD RUNCMD]") == 1


def test_lightcone_status_has_only_requested_boundary_materialized() -> None:
    result = subprocess.run(
        ["lc", "status", "--json"],
        cwd=PROJECT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    outputs = {output["output"]: output["status"] for output in payload["outputs"]}
    assert set(outputs) == {
        "baseline/best_fit",
        "baseline/hubble_diagram",
        "baseline/residuals",
        "baseline/bootstrap_intervals",
    }
    assert {name for name, status in outputs.items() if status == "current"} == {
        "baseline/best_fit"
    }


def test_no_async_record_or_downstream_output_was_created() -> None:
    jobs = PROJECT / ".lightcone/jobs"
    assert not jobs.exists() or not any(jobs.iterdir())
    assert_unrequested_outputs_absent()
