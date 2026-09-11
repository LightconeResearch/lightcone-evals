from __future__ import annotations

import json
import subprocess

import yaml

from _util import PROJECT, SPEC_PATH


def _run_validate(*extra_args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["astra", "validate", str(SPEC_PATH), "--json", *extra_args],
        cwd=PROJECT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_spec_exists() -> None:
    assert SPEC_PATH.is_file(), "astra.yaml was not authored at the project root"


def test_astra_validate_passes_schema_and_semantics() -> None:
    result = _run_validate()
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert "Schema validation passed" in report
    assert "Semantic validation passed" in report


def test_spec_declares_a_data_input() -> None:
    spec = yaml.safe_load(SPEC_PATH.read_text())
    inputs = spec.get("inputs") or []
    assert any(item.get("type") == "data" for item in inputs), "no data input declared"


def test_spec_declares_a_metric_output_with_a_recipe() -> None:
    spec = yaml.safe_load(SPEC_PATH.read_text())
    outputs = spec.get("outputs") or []
    metrics = [output for output in outputs if output.get("type") == "metric"]
    assert metrics, "no metric output declared"
    assert any((m.get("recipe") or {}).get("command") for m in metrics), (
        "no metric output declares a recipe command"
    )


def test_spec_declares_a_figure_output_with_a_recipe() -> None:
    # Deliberately does NOT require the figure to depend on another declared
    # output (e.g. the metric): neither instruction file asks for a
    # particular dependency structure, and an agent computing the fit
    # inline inside the figure's own recipe is a perfectly valid ASTRA spec
    # that `astra validate` accepts. See check_figure_dependency.py for that
    # structure recorded as a non-scoring diagnostic instead.
    spec = yaml.safe_load(SPEC_PATH.read_text())
    outputs = spec.get("outputs") or []
    figures = [output for output in outputs if output.get("type") == "figure"]
    assert figures, "no figure output declared"
    assert any((f.get("recipe") or {}).get("command") for f in figures), (
        "no figure output declares a recipe command"
    )
