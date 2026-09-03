from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile
import time
from pathlib import Path

import pytest
import yaml
from jsonschema import Draft202012Validator

PROJECT = Path(os.environ.get("TASK_PROJECT_ROOT", "/root/snae"))
OUTPUTS = ("best_fit", "hubble_diagram", "residuals")
RESOURCE_KEYS = {"cpus", "memory", "time_limit"}


# ASTRA documents memory as a string with units ("8GB", "512Mi", "16Gi") and
# time_limit as a duration string ("2h", "30m", "1h30m"); accept those forms.
_MEMORY_MB = {
    "B": 1e-6, "KB": 1e-3, "MB": 1.0, "GB": 1e3, "TB": 1e6,
    "K": 1e-3, "M": 1.0, "G": 1e3, "T": 1e6,
    "KI": 1.024e-3, "MI": 1.048576, "GI": 1073.741824, "TI": 1099511.627776,
    "KIB": 1.024e-3, "MIB": 1.048576, "GIB": 1073.741824, "TIB": 1099511.627776,
}


def memory_mb(value: str) -> float:
    match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*([A-Za-z]+)\s*", str(value))
    assert match and match.group(2).upper() in _MEMORY_MB, f"Unsupported memory value: {value!r}"
    return float(match.group(1)) * _MEMORY_MB[match.group(2).upper()]


def time_seconds(value: str) -> float:
    text = str(value).strip()
    clock = re.fullmatch(r"(?:(\d+)-)?(\d+):(\d\d):(\d\d)", text)
    if clock:
        days, hours, minutes, seconds = (int(part or 0) for part in clock.groups())
        return days * 86400 + hours * 3600 + minutes * 60 + seconds
    parts = re.findall(r"(\d+(?:\.\d+)?)\s*([dhms])", text, re.I)
    assert parts and re.fullmatch(r"(?:\s*\d+(?:\.\d+)?\s*[dhms])+\s*", text, re.I), (
        f"Unsupported time_limit value: {value!r}"
    )
    factor = {"d": 86400, "h": 3600, "m": 60, "s": 1}
    return sum(float(number) * factor[unit.lower()] for number, unit in parts)


@pytest.fixture(scope="module")
def spec() -> dict:
    return yaml.safe_load((PROJECT / "astra.yaml").read_text())


@pytest.fixture(scope="module")
def resources(spec: dict) -> dict[str, dict]:
    return {
        output["id"]: output["recipe"].get("resources", {})
        for output in spec["outputs"]
        if output["id"] in OUTPUTS
    }


@pytest.fixture(scope="module")
def record() -> dict:
    return json.loads((PROJECT / ".lightcone" / "estimates.json").read_text())


def test_estimate_record_matches_supplied_schema(record: dict) -> None:
    schema = json.loads((PROJECT / "estimate-record.schema.json").read_text())
    Draft202012Validator(schema).validate(record)


def test_astra_validates() -> None:
    result = subprocess.run(
        # The pip-installed astra-tools==0.2.13 entry point is root-owned; the
        # uvx cache the agent uses is writable by the agent and must not grade.
        ["astra", "validate", str(PROJECT / "astra.yaml")],
        cwd=PROJECT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_every_recipe_has_only_supported_resources(resources: dict[str, dict]) -> None:
    assert set(resources) == set(OUTPUTS)
    for output_name, declared in resources.items():
        # astra-spec rejects gpus: 0, so a GPU-free recipe declares no gpus key.
        assert set(declared) == RESOURCE_KEYS, f"{output_name}: {declared}"
        assert declared["cpus"] == 1
        assert declared.get("gpus", 0) == 0


def test_requests_are_safe_and_not_absurd(resources: dict[str, dict]) -> None:
    for output_name, declared in resources.items():
        assert 128 <= memory_mb(declared["memory"]) <= 4096, output_name
        assert 10 <= time_seconds(declared["time_limit"]) <= 900, output_name


def test_estimate_record_covers_target_and_local_capacity(record: dict) -> None:
    assert record["schema_version"] == 1
    assert record["target"]["universe"] == "baseline"
    assert set(record["target"]["outputs"]) == set(OUTPUTS)
    assert record["environment"]["kind"] == "local"
    assert record["environment"]["cpus_available"] >= 1
    assert record["environment"]["memory_mb_available"] > 0
    assert record["environment"]["gpus_available"] == 0


def test_evidence_is_auditable_and_matches_astra(record: dict, resources: dict[str, dict]) -> None:
    estimates = {estimate["output"]: estimate for estimate in record["estimates"]}
    assert set(estimates) == set(OUTPUTS)
    for output_name, estimate in estimates.items():
        assert estimate["basis"] in {"measured", "static"}
        assert estimate["evidence"]
        assert str(estimate["model"]).strip()
        assert estimate["safety_factors"]["walltime"] >= 1.5
        assert estimate["safety_factors"]["memory"] >= 1.25
        assert estimate["request"] == resources[output_name]


def test_declared_envelopes_cover_independent_runs(resources: dict[str, dict]) -> None:
    with tempfile.TemporaryDirectory(prefix="snae-verifier-") as raw_tmp:
        tmp = Path(raw_tmp)
        fit = tmp / "best_fit"
        commands = {
            "best_fit": [
                "python",
                "scripts/fit.py",
                "--data",
                "data/SCPUnion2.1_mu_vs_z.txt",
                "--output",
                str(fit),
                "--optimizer",
                "nelder_mead",
                "--error-model",
                "stat_and_sys",
                "--redshift-cut",
                "z_min_001",
            ],
            "hubble_diagram": [
                "python",
                "scripts/plot_hubble.py",
                "--data",
                "data/SCPUnion2.1_mu_vs_z.txt",
                "--fit",
                str(fit),
                "--output",
                str(tmp / "hubble"),
            ],
            "residuals": [
                "python",
                "scripts/plot_residuals.py",
                "--data",
                "data/SCPUnion2.1_mu_vs_z.txt",
                "--fit",
                str(fit),
                "--output",
                str(tmp / "residuals"),
            ],
        }
        for output_name, command in commands.items():
            started = time.perf_counter()
            result = subprocess.run(
                ["/usr/bin/time", "-v", *command],
                cwd=PROJECT,
                text=True,
                capture_output=True,
                check=False,
            )
            elapsed = time.perf_counter() - started
            assert result.returncode == 0, result.stderr or result.stdout
            match = re.search(r"Maximum resident set size \(kbytes\):\s*(\d+)", result.stderr)
            assert match, "peak RSS was not reported"
            measured_memory_mb = int(match.group(1)) / 1000
            declared = resources[output_name]
            # The agent applied its safety factors to its own measurement; this
            # independent run must merely fit inside the declared envelope, or a
            # correct estimate fails on a slower or busier verifier host.
            assert memory_mb(declared["memory"]) >= measured_memory_mb, output_name
            assert time_seconds(declared["time_limit"]) >= elapsed, output_name


def test_estimation_did_not_materialize_unrequested_outputs() -> None:
    baseline = PROJECT / "results" / "baseline"
    assert not (baseline / "hubble_diagram").exists()
    assert not (baseline / "residuals").exists()
    assert not (baseline / "bootstrap_intervals").exists()
