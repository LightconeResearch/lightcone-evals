from __future__ import annotations

import re
import subprocess

import yaml

from _util import PROJECT, SPEC_PATH

# Both DOI forms refer to the same paper (Suzuki et al. 2012): the arXiv
# preprint we pre-cache, and the journal's own DOI. An insight citing either
# is "about Suzuki's own result" regardless of which the agent used.
_SUZUKI_DOIS = {"10.48550/arxiv.1105.3470", "10.1088/0004-637x/746/1/85"}

_VERIFICATION_RAN_RE = re.compile(r"(\d+)\s*/\s*(\d+)\s+verified", re.I)
_FAILED_EVIDENCE_ID_RE = re.compile(r"!\s+(\S+):", re.I)


def _suzuki_evidence_ids(spec: dict) -> set[str]:
    """Evidence ids, across all prior_insights, that cite Suzuki et al. 2012."""
    ids: set[str] = set()
    for insight in (spec.get("prior_insights") or {}).values():
        for evidence in insight.get("evidence") or []:
            doi = str(evidence.get("doi") or "").strip().lower()
            evidence_id = evidence.get("id")
            if doi in _SUZUKI_DOIS and evidence_id:
                ids.add(str(evidence_id))
    return ids


def test_at_least_one_suzuki_prior_insight_evidence_is_verified() -> None:
    # The prompt asks the agent to record the paper's own constraint with
    # evidence -- not to cite nothing else, and not to keep everything it
    # cites verifiable. An extra, unrequested citation to a paper we can't
    # fetch (see verifier.md's caveat on this environment's evidence
    # verification) must not sink this dimension if the REQUIRED claim
    # itself verifies. So: find the evidence id(s) that cite Suzuki's own
    # paper, then check only those against --verify-evidence's report,
    # rather than requiring every prior_insight in the spec to verify.
    spec = yaml.safe_load(SPEC_PATH.read_text())
    candidate_ids = _suzuki_evidence_ids(spec)
    assert candidate_ids, (
        "no prior_insight cites Suzuki et al. 2012 (DOI 10.48550/arXiv.1105.3470 "
        "or 10.1088/0004-637X/746/1/85) about their own Omega_Lambda constraint"
    )

    result = subprocess.run(
        ["astra", "validate", str(SPEC_PATH), "--verify-evidence"],
        cwd=PROJECT,
        text=True,
        capture_output=True,
        check=False,
    )
    report = result.stdout + result.stderr
    assert _VERIFICATION_RAN_RE.search(report), (
        "evidence verification did not run (validate likely aborted earlier, "
        f"e.g. on schema/semantic errors): {report!r}"
    )
    failed_ids = {evidence_id.lower() for evidence_id in _FAILED_EVIDENCE_ID_RE.findall(report)}
    verified_candidates = {i for i in candidate_ids if i.lower() not in failed_ids}
    assert verified_candidates, (
        f"every Suzuki-citing prior_insight evidence failed verification "
        f"({candidate_ids}): {report!r}"
    )


def _option_text(option_id: str, option: dict) -> str:
    fields = " ".join(str(option.get(field, "")) for field in ("label", "description"))
    return f"{option_id} {fields}".lower()


# Matching only the SELECTED (default) option's own text for an affirmative
# signal, rather than pattern-matching every option's prose and excluding by
# the absence of a word: a natural description of a statistics-only option
# ("...ignoring systematic uncertainties") legitimately mentions the word
# "systematic" while describing the opposite choice, which broke an earlier
# version of this matcher (false negative on a perfectly good spec). The
# covmat_sys filename is the most robust signal available when prose alone
# is ambiguous.
_SYSTEMATIC_AFFIRMATIVE_HINTS = ("system", "covmat_sys")
_MARGINALIZED_AFFIRMATIVE_HINTS = ("margin",)


def _selected_option_text(decision: dict) -> str | None:
    options = decision.get("options") or {}
    if len(options) < 2:
        return None
    default_id = decision.get("default")
    if not default_id or default_id not in options:
        return None
    return _option_text(default_id, options[default_id])


def _decision_selects_systematics_covariance(decision: dict) -> bool:
    text = _selected_option_text(decision)
    if text is None:
        return False
    return any(hint in text for hint in _SYSTEMATIC_AFFIRMATIVE_HINTS)


def test_spec_records_a_decision_choosing_the_systematics_covariance() -> None:
    spec = yaml.safe_load(SPEC_PATH.read_text())
    decisions = spec.get("decisions") or {}
    assert decisions, "no decisions declared in astra.yaml"
    assert any(_decision_selects_systematics_covariance(d) for d in decisions.values()), (
        "no decision was found with >=2 options whose selected (default) "
        "option's own text affirmatively indicates the systematics-inclusive "
        "covariance"
    )


def _decision_selects_marginalized_magnitude(decision: dict) -> bool:
    text = _selected_option_text(decision)
    if text is None:
        return False
    return any(hint in text for hint in _MARGINALIZED_AFFIRMATIVE_HINTS)


def test_spec_records_a_decision_choosing_marginalized_magnitude() -> None:
    spec = yaml.safe_load(SPEC_PATH.read_text())
    decisions = spec.get("decisions") or {}
    assert decisions, "no decisions declared in astra.yaml"
    assert any(_decision_selects_marginalized_magnitude(d) for d in decisions.values()), (
        "no decision was found with >=2 options whose selected (default) "
        "option's own text affirmatively indicates marginalized SN absolute "
        "magnitude"
    )
