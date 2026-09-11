"""The two ASTRA dimensions, each 0/1.

Every verdict here comes from the pinned astra-tools CLI in the image
(`astra validate`, `astra paper verify-quote`) and is read from its exit
code — never re-derived from parsed YAML. The only YAML this module reads is
for the three nouns the prompt literally names (inputs, outputs, choices),
which astra-tools 0.2.17 does not itself require, and for locating the
evidence items to hand to the CLI.

Licensed by instruction-astra.md only; under tier A these legitimately score
0 for an agent doing perfect unassisted science, and contribute nothing to
that tier's reward (see test.sh).
"""

from __future__ import annotations

import subprocess

import yaml

from _util import PROJECT, SPEC_PATH

# Suzuki et al. 2012 can be cited by its arXiv id (which is how the prompt
# itself names the paper, in any of the doi/arXiv spellings that embed it) or
# by the journal's own DOI. Either identifies the same paper -- but the image
# caches it under the arXiv DOI only (environment/Dockerfile), so a journal
# citation is verified against that cached copy rather than failing as
# "not in cache" for choosing the other legitimate identifier.
_SUZUKI_ARXIV_ID = "1105.3470"
_SUZUKI_ARXIV_DOI = "10.48550/arXiv.1105.3470"
_SUZUKI_JOURNAL_DOI = "10.1088/0004-637x/746/1/85"


def test_spec_valid() -> None:
    # `astra validate`'s exit code is the verdict, and it already carries
    # schema validity, decision `default in options`, `default` not excluded,
    # and `when`/`from` reference resolution. Re-deriving any of that from
    # the YAML would re-implement a check the CLI performs.
    result = subprocess.run(
        ["astra", "validate", str(SPEC_PATH)],
        cwd=PROJECT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr

    # ...plus exactly the prompt's three nouns: "an `astra.yaml` capturing
    # the inputs, the outputs and the choices made along the way".
    # astra-tools 0.2.17 requires none of these three to be non-empty, so
    # they are asserted here and nowhere else. Deliberately NOT asserted:
    # `type:` tokens, recipes, dependency shape, or particular decision IDs.
    spec = yaml.safe_load(SPEC_PATH.read_text())
    assert spec.get("inputs"), "no inputs declared"
    assert spec.get("outputs"), "no outputs declared"
    assert spec.get("decisions"), "no decisions declared"


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
            doi = str(evidence.get("doi") or "").strip()
            if quote and (_SUZUKI_ARXIV_ID in doi.lower() or doi.lower() == _SUZUKI_JOURNAL_DOI):
                if doi.lower() == _SUZUKI_JOURNAL_DOI:
                    doi = _SUZUKI_ARXIV_DOI
                items.append({"doi": doi, "quote": quote, "version": evidence.get("version")})
    return items


def test_evidence_verified() -> None:
    # The prompt asks the agent to record the paper's own constraint with
    # evidence -- not to cite nothing else, and not to keep everything it
    # cites verifiable. An extra, unrequested citation to a paper we can't
    # fetch (see verifier.md's caveat on this environment's evidence cache)
    # must not sink this dimension if the REQUIRED claim itself verifies.
    # That is also why this is not `astra validate --verify-evidence`, which
    # is all-or-nothing across every evidence item. So: find the evidence
    # citing Suzuki's own paper and ask the CLI that already decides this
    # question -- `astra paper verify-quote`, whose exit code is the verdict
    # (0 verified, 1 not found, 2 not cached).
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
