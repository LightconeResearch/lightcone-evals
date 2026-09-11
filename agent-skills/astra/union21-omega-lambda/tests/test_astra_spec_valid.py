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


def test_spec_declares_inputs_and_outputs() -> None:
    # The prompt asks for a spec "capturing the inputs, the outputs and the
    # choices made along the way", so that -- and nothing beyond it -- is
    # what this asserts. Deliberately NOT asserted: which `type:` token an
    # input or output carries (`data` vs `metric` vs `table` vs `figure` are
    # all legal for these artifacts and the prompt names none of them), and
    # whether the figure output depends on the metric output (a structural
    # opinion the prompt never states; computing the fit inline inside the
    # figure's recipe is a spec `astra validate` accepts).
    spec = yaml.safe_load(SPEC_PATH.read_text())
    assert spec.get("inputs"), "no inputs declared"
    assert spec.get("outputs"), "no outputs declared"
