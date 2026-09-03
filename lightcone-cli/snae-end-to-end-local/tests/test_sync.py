from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import numpy as np

PROJECT = Path(os.environ.get("TASK_PROJECT_ROOT", "/root/snae"))
OUTPUT = PROJECT / "results" / "baseline" / "best_fit"


def test_best_fit_artifacts_exist() -> None:
    assert (OUTPUT / "best_fit.json").is_file()
    assert (OUTPUT / "fitted_model.csv").is_file()
    assert (OUTPUT / ".lightcone-manifest.json").is_file()


def test_fit_is_physically_and_internally_reasonable() -> None:
    fit = json.loads((OUTPUT / "best_fit.json").read_text())
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
        PROJECT / "data" / "SCPUnion2.1_mu_vs_z.txt",
        comments="#",
        usecols=(1,),
    )
    expected_rows = int(np.count_nonzero(raw > 0.01))
    fit = json.loads((OUTPUT / "best_fit.json").read_text())
    model = np.loadtxt(OUTPUT / "fitted_model.csv", delimiter=",", skiprows=1)
    assert fit["n_supernovae"] == expected_rows
    assert model.shape == (expected_rows, 5)
    assert np.all(np.isfinite(model))


def test_manifest_records_local_lightcone_provenance() -> None:
    manifest = json.loads((OUTPUT / ".lightcone-manifest.json").read_text())
    assert manifest["output_id"] == "best_fit"
    assert manifest["universe_id"] == "baseline"
    assert manifest["slurm_job_id"] is None
    assert manifest["lc_version"]
    assert manifest["recipe"]
    assert set(manifest["decisions"]) == {"optimizer", "error_model", "redshift_cut"}
    assert "union21" in manifest["input_versions"]


def test_lightcone_status_has_only_requested_boundary_materialized() -> None:
    result = subprocess.run(
        ["lc", "status", "--universe", "baseline", "--json"],
        cwd=PROJECT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    payload = json.loads(result.stdout)
    outputs = {
        output["output_id"]: output["status"]
        for universe in payload["universes"]
        for output in universe["outputs"]
    }
    assert outputs["best_fit"] == "ok"
    assert outputs["hubble_diagram"] == "missing"
    assert outputs["residuals"] == "missing"
    assert outputs["bootstrap_intervals"] == "missing"


def test_no_async_record_or_downstream_output_was_created() -> None:
    jobs = PROJECT / ".lightcone" / "jobs"
    assert not jobs.exists() or not any(jobs.iterdir())
    assert not (PROJECT / "results" / "baseline" / "hubble_diagram").exists()
    assert not (PROJECT / "results" / "baseline" / "residuals").exists()
    assert not (PROJECT / "results" / "baseline" / "bootstrap_intervals").exists()
