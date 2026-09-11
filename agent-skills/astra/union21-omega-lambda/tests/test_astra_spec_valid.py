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


def test_spec_declares_a_downstream_figure_output_with_a_recipe() -> None:
    spec = yaml.safe_load(SPEC_PATH.read_text())
    outputs = spec.get("outputs") or []
    output_ids = {output["id"] for output in outputs if "id" in output}
    figures = [output for output in outputs if output.get("type") == "figure"]
    assert figures, "no figure output declared"

    def depends_on_another_output(figure: dict) -> bool:
        upstream = set(figure.get("inputs") or [])
        return bool(upstream & (output_ids - {figure.get("id")}))

    downstream = [figure for figure in figures if depends_on_another_output(figure)]
    assert downstream, "no figure output depends on another declared output"
    assert any((f.get("recipe") or {}).get("command") for f in downstream), (
        "the downstream figure output declares no recipe command"
    )
