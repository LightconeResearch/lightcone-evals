from __future__ import annotations

import json
import re
import subprocess

import yaml

from _util import PROJECT, SPEC_PATH

_VERIFIED_RE = re.compile(r"(\d+)/(\d+)\s+verified", re.I)

_SYSTEMATIC_HINTS = ("system",)
_STATISTICAL_ONLY_HINTS = ("statistic", "nosys", "no_sys", "no-sys", "without")

_MARGINALIZED_HINTS = ("margin",)
_FIXED_HINTS = ("fixed", "no_margin", "not_marginal", "without")


def test_prior_insight_evidence_is_fully_verified() -> None:
    result = subprocess.run(
        ["astra", "validate", str(SPEC_PATH), "--verify-evidence", "--json"],
        cwd=PROJECT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    match = _VERIFIED_RE.search(report)
    assert match, f"no evidence verification summary found in: {report!r}"
    verified, total = int(match.group(1)), int(match.group(2))
    assert total >= 1, "no prior-insight evidence was declared to verify"
    assert verified == total, f"only {verified}/{total} evidence quote(s) verified"


def _option_text(option_id: str, option: dict) -> str:
    fields = " ".join(str(option.get(field, "")) for field in ("label", "description"))
    return f"{option_id} {fields}".lower()


def _decision_selects_systematics_covariance(decision: dict) -> bool:
    options = decision.get("options") or {}
    if len(options) < 2:
        return False
    texts = {option_id: _option_text(option_id, option) for option_id, option in options.items()}
    has_systematics_option = any(
        any(hint in text for hint in _SYSTEMATIC_HINTS) for text in texts.values()
    )
    has_statistical_only_option = any(
        any(hint in text for hint in _STATISTICAL_ONLY_HINTS) and "system" not in text
        for text in texts.values()
    )
    if not (has_systematics_option and has_statistical_only_option):
        return False
    default_id = decision.get("default")
    default_text = texts.get(default_id, "")
    return any(hint in default_text for hint in _SYSTEMATIC_HINTS)


def test_spec_records_a_decision_choosing_the_systematics_covariance() -> None:
    spec = yaml.safe_load(SPEC_PATH.read_text())
    decisions = spec.get("decisions") or {}
    assert decisions, "no decisions declared in astra.yaml"
    assert any(_decision_selects_systematics_covariance(d) for d in decisions.values()), (
        "no decision was found offering both a statistical-only and a "
        "systematics-inclusive covariance option with the latter selected "
        "as the default"
    )


def _decision_selects_marginalized_magnitude(decision: dict) -> bool:
    options = decision.get("options") or {}
    if len(options) < 2:
        return False
    texts = {option_id: _option_text(option_id, option) for option_id, option in options.items()}
    has_marginalized_option = any(
        any(hint in text for hint in _MARGINALIZED_HINTS) for text in texts.values()
    )
    has_fixed_option = any(
        any(hint in text for hint in _FIXED_HINTS) and "margin" not in text
        for text in texts.values()
    )
    if not (has_marginalized_option and has_fixed_option):
        return False
    default_id = decision.get("default")
    default_text = texts.get(default_id, "")
    return any(hint in default_text for hint in _MARGINALIZED_HINTS)


def test_spec_records_a_decision_choosing_marginalized_magnitude() -> None:
    spec = yaml.safe_load(SPEC_PATH.read_text())
    decisions = spec.get("decisions") or {}
    assert decisions, "no decisions declared in astra.yaml"
    assert any(_decision_selects_marginalized_magnitude(d) for d in decisions.values()), (
        "no decision was found offering both a fixed and a marginalized "
        "SN absolute-magnitude treatment with the latter selected as the "
        "default"
    )
