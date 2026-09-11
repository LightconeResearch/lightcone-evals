from __future__ import annotations

import subprocess

import yaml

from _util import PROJECT, SPEC_PATH


def test_astra_validate_passes_schema_and_semantics() -> None:
    # `astra validate`'s exit code is the verdict; re-deriving it from the
    # report's prose would be re-implementing a check the CLI already
    # performs. The plain-text report is the better failure message anyway.
    result = subprocess.run(
        ["astra", "validate", str(SPEC_PATH)],
        cwd=PROJECT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_spec_declares_a_data_input() -> None:
    spec = yaml.safe_load(SPEC_PATH.read_text())
    inputs = spec.get("inputs") or []
    assert any(item.get("type") == "data" for item in inputs), "no data input declared"


def test_spec_declares_a_metric_output() -> None:
    spec = yaml.safe_load(SPEC_PATH.read_text())
    outputs = spec.get("outputs") or []
    assert any(output.get("type") == "metric" for output in outputs), "no metric output declared"


def test_spec_declares_a_figure_output() -> None:
    # Deliberately does NOT require the figure to depend on another declared
    # output (e.g. the metric): neither instruction file asks for a
    # particular dependency structure, and an agent computing the fit
    # inline inside the figure's own recipe is a perfectly valid ASTRA spec
    # that `astra validate` accepts.
    spec = yaml.safe_load(SPEC_PATH.read_text())
    outputs = spec.get("outputs") or []
    assert any(output.get("type") == "figure" for output in outputs), "no figure output declared"
