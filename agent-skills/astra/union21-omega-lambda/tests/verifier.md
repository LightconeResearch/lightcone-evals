---
document_version: '0.3'
verifier:
  name: union21-omega-lambda-verifier
  default_strategy: pytest
  strategies:
    pytest:
      type: script
      command: ./test.sh
  rubric:
    combine: weighted_sum
    dimensions:
      spec_validity:
        weight: 0.15
        source: pytest
      analysis_executed:
        weight: 0.15
        source: pytest
      fit_correct:
        weight: 0.15
        source: pytest
      systematics_covariance:
        weight: 0.20
        source: pytest
      paper_reproduced:
        weight: 0.20
        source: pytest
      evidence_and_decision:
        weight: 0.15
        source: pytest
  outputs:
    reward_text: /logs/verifier/reward.txt
    reward_json: /logs/verifier/reward.json
---

## verifier intent

Six dimensions scored as a progress ladder, not a flat checklist. The
instruction never says "ASTRA" — this is tier A of a three-tier ablation
(no ASTRA / ASTRA named / ASTRA named + plugin), so `spec_validity` and
`evidence_and_decision` measure whether the agent reaches for ASTRA
unprompted, and scoring zero on them is an expected, informative outcome for
an agent that solves the physics without ever authoring a spec.

`spec_validity` checks that `astra.yaml` is schema- and semantically-valid
and declares a data input, a metric output, and a downstream figure output,
each with a recipe command. `analysis_executed` checks that the analysis
actually ran — a machine-readable best-fit artifact and a non-trivial,
decodable Hubble-diagram PNG exist somewhere under the project.

`fit_correct`, `systematics_covariance`, and `paper_reproduced` are three
rungs of the same ladder, deliberately nested rather than independent
levels of a single check, because they fail for different reasons:
- `fit_correct` only asks whether the flat-LCDM fit itself is right, under
  any covariance and any magnitude treatment.
- `systematics_covariance` asks whether the agent additionally found the
  systematics-inclusive covariance matrix over the statistics-only one (the
  first seeded defect) — visible as the recorded uncertainty widening from
  ~0.013-0.02 to ~0.03-0.05, independent of the magnitude treatment.
- `paper_reproduced` asks whether the agent found *both* seeded defects
  together — the systematics covariance AND analytic marginalization over
  the SN absolute magnitude — by requiring a single recorded estimate whose
  value AND uncertainty both fall in the paper-comparable window
  (Omega_Lambda in [0.697, 0.712], sigma in [0.036, 0.046]). Checking the
  pair on the same record, not just each bound separately across whatever
  files exist, is what stops two unrelated numbers from being credited as a
  reproduction.

`evidence_and_decision` checks that the paper's Omega_Lambda constraint was
verified as evidence, AND that the spec's `decisions:` block names both
choices — the covariance decision with its systematics-inclusive option
selected, and the magnitude-treatment decision with its marginalized option
selected.

The agent authors astra.yaml from scratch (if it authors one at all) and
chooses its own output layout, so the physics dimensions never hardcode a
file path or JSON key: they glob every JSON/YAML file under the project
(excluding `data/` and the spec itself) and pattern-match on keys that look
like an Omega_Lambda value or its uncertainty (`_util.py`'s
`_OMEGA_KEY`/`_SIGMA_KEY` regexes), and the decision checks pattern-match
option text for "systematic"/"statistical" and "marginalize"/"fixed" rather
than requiring specific IDs. What's checked strictly is the physics (the
recovered value and uncertainty must fall in narrow, paper-informed windows)
and the validation outcomes (`astra validate` and `--verify-evidence` must
both report full success). A task that never touches ASTRA, guesses wrong on
either seeded defect, or never runs the analysis fails on exactly the
dimensions that show it, independent of the others.
