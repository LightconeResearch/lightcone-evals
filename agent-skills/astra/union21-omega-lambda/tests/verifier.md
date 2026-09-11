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
    combine: ordinal_level_plus_out_of_band_flags
    reward_formula: "science_level / 3"
    ordinal:
      science_level:
        range: [0, 3]
        source: pytest
        levels:
          0: "no working fit"
          1: "recorded Omega_Lambda in [0.690, 0.735] AND a valid non-trivial Hubble diagram PNG"
          2: "level 1, AND recorded 1-sigma in [0.025, 0.050] (systematics covariance found)"
          3: "level 2, AND recorded Omega_Lambda in [0.697, 0.712] AND 1-sigma in [0.036, 0.046] on the same estimate (paper reproduced)"
    out_of_band_flags:
      astra_spec_valid:
        range: [0, 1]
        source: pytest
        reward_contribution: none
      astra_evidence_and_decisions:
        range: [0, 1]
        source: pytest
        reward_contribution: none
  outputs:
    reward_text: /logs/verifier/reward.txt
    reward_json: /logs/verifier/reward.json
---

## verifier intent

This task no longer fits the `combine: weighted_sum` / independent-dimensions
shape the template assumes, and the rubric block above says so explicitly
rather than inventing weights that happen to reproduce a number. Two changes
from a flat weighted rubric, and why:

**`science_level` is one ordinal 0-3, not three weighted dimensions.**
`fit_correct` -> `systematics_covariance` -> `paper_reproduced` are strictly
nested: you cannot reach level 3 without level 2, or level 2 without level
1. That is a single ladder of scientific progress, not three independent
things needing relative importances nobody could actually justify (why would
finding the systematics covariance be worth more than a working fit but less
than a full reproduction, and by how much?). `reward = science_level / 3` is
the entire formula — nothing else is summed in. The old `analysis_executed`
dimension (a valid, non-trivial Hubble diagram PNG) is absorbed into level 1,
since a fit without a figure to show for it isn't yet a completed piece of
science at any level.

**`astra_spec_valid` and `astra_evidence_and_decisions` are reported, never
scored.** This task is tier A of a three-tier ablation (no ASTRA / ASTRA
named / ASTRA named + plugin) — the instruction never says "ASTRA" at all,
so these two flags measure whether an agent reaches for it unprompted (tier
A) or whether the plugin makes the difference (tier C). Both legitimately
score 0 for a baseline agent doing perfect, unassisted science, and that is
exactly the point: folding them into the reward would mean tier A caps at
some reward less than 1.0 however good the science is, making its number
incomparable to tier C's. Keeping them out-of-band is what makes
`science_level` the one number that means the same thing in every tier.

`astra_spec_valid` checks that `astra.yaml` is schema- and
semantically-valid and declares a data input, a metric output, and a
downstream figure output, each with a recipe command.
`astra_evidence_and_decisions` checks that the paper's Omega_Lambda
constraint was verified as evidence AND that the spec's `decisions:` block
names both choices — the covariance decision with its systematics-inclusive
option selected, and the magnitude-treatment decision with its marginalized
option selected.

The agent authors astra.yaml from scratch (if it authors one at all) and
chooses its own output layout, so the physics tests never hardcode a file
path or JSON key: they glob every JSON/YAML file under the project
(excluding `data/` and the spec itself) and pattern-match on keys that look
like an Omega_Lambda value or its uncertainty (`_util.py`'s
`_OMEGA_KEY`/`_SIGMA_KEY` regexes), and the decision checks pattern-match
option text for "systematic"/"statistical" and "marginalize"/"fixed" rather
than requiring specific IDs. What's checked strictly is the physics (the
recovered value and uncertainty must fall in narrow, paper-informed windows,
and level 3's pairing must hold on a single recorded estimate, not two
unrelated numbers) and the validation outcomes (`astra validate` and
`--verify-evidence` must both report full success).

Each level's pytest module checks only its own incremental condition — level
2's module does not re-check level 1's fit, level 3's does not re-check
level 2's uncertainty window — because `test.sh` only advances the ladder
while the previous rung already passed, enforcing the nesting structurally
rather than by re-testing or by weighting.
