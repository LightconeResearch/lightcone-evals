from __future__ import annotations

import subprocess

import yaml

from _util import PROJECT, SPEC_PATH

# Suzuki et al. 2012 can be cited by its arXiv id (which is how the prompt
# itself names the paper, in any of the doi/arXiv spellings that embed it) or
# by the journal's own DOI. Either identifies the same paper.
_SUZUKI_ARXIV_ID = "1105.3470"
_SUZUKI_JOURNAL_DOI = "10.1088/0004-637x/746/1/85"


def _cites_suzuki(doi: str) -> bool:
    doi = doi.strip().lower()
    return _SUZUKI_ARXIV_ID in doi or doi == _SUZUKI_JOURNAL_DOI


def _insights(spec: dict):
    """Every insight record, whether filed under prior_insights or findings.

    `astra validate --verify-evidence` verifies evidence identically under
    both keys, and the prompt names neither, so neither does this check.
    """
    for section in ("prior_insights", "findings"):
        value = spec.get(section) or {}
        yield from (value.values() if isinstance(value, dict) else value)


def _suzuki_evidence(spec: dict) -> list[dict]:
    """Evidence items citing Suzuki et al. 2012, with the quote to verify."""
    items = []
    for insight in _insights(spec):
        for evidence in (insight or {}).get("evidence") or []:
            quote = ((evidence.get("quote") or {}).get("exact") or "").strip()
            if quote and _cites_suzuki(str(evidence.get("doi") or "")):
                items.append(
                    {
                        "doi": str(evidence["doi"]).strip(),
                        "quote": quote,
                        "version": evidence.get("version"),
                    }
                )
    return items


def test_at_least_one_suzuki_evidence_quote_verifies() -> None:
    # The prompt asks the agent to record the paper's own constraint with
    # evidence -- not to cite nothing else, and not to keep everything it
    # cites verifiable. An extra, unrequested citation to a paper we can't
    # fetch (see verifier.md's caveat on this environment's evidence
    # verification) must not sink this dimension if the REQUIRED claim
    # itself verifies. So: find the evidence citing Suzuki's own paper and
    # ask the CLI that already decides this question -- `astra paper
    # verify-quote`, whose exit code is the verdict (0 verified, 1 not
    # found, 2 not cached).
    spec = yaml.safe_load(SPEC_PATH.read_text())
    candidates = _suzuki_evidence(spec)
    assert candidates, (
        f"no evidence quote cites Suzuki et al. 2012 (arXiv {_SUZUKI_ARXIV_ID} "
        f"or DOI {_SUZUKI_JOURNAL_DOI}) about their own Omega_Lambda constraint"
    )

    reports = []
    for item in candidates:
        command = ["astra", "paper", "verify-quote", item["doi"], "-q", item["quote"]]
        if item["version"] is not None:
            command += ["-v", str(item["version"])]
        result = subprocess.run(
            [*command, "--json"], cwd=PROJECT, text=True, capture_output=True, check=False
        )
        if result.returncode == 0:
            return
        reports.append(f"{item['doi']}: rc={result.returncode} {result.stdout}{result.stderr}")

    raise AssertionError(
        "no Suzuki-citing evidence quote verified against the paper:\n" + "\n".join(reports)
    )


def test_spec_records_a_decision_with_a_selected_option() -> None:
    # The prompt asks for "the choices made along the way" -- the choices the
    # agent actually made. Which particular ones it made is science_level's
    # question, not this flag's; requiring specific decisions here would
    # measure the science a second time inside the ASTRA dimension and
    # confound the ablation.
    spec = yaml.safe_load(SPEC_PATH.read_text())
    decisions = spec.get("decisions") or {}
    assert decisions, "no decisions declared in astra.yaml"
    assert any(
        (d.get("default") is not None) and d.get("default") in (d.get("options") or {})
        for d in decisions.values()
    ), "no decision records a default that resolves to one of its own options"
