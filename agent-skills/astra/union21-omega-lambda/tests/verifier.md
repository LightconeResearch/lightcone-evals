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
    combine: ordinal_level_plus_astra_flags_weighted_sum
    reward_formula: "0.6 * (science_level / 3) + 0.2 * astra_spec_valid + 0.2 * astra_evidence_and_decisions"
    ordinal:
      science_level:
        range: [0, 3]
        source: pytest
        weight_in_reward: 0.6
        # The four numeric windows below restate tests/tolerances.json for
        # readability. That file (and environment/project/contract.json for
        # the paths/keys) is authoritative if the two ever disagree.
        levels:
          0: "no working fit"
          1: "recorded Omega_Lambda in [0.690, 0.735] AND a valid non-trivial Hubble diagram PNG"
          2: "level 1, AND recorded 1-sigma in [0.025, 0.050] (systematics covariance found)"
          3: "level 2, AND recorded Omega_Lambda in [0.697, 0.712] AND 1-sigma in [0.036, 0.046] on the same estimate (paper reproduced)"
    astra_flags:
      astra_spec_valid:
        range: [0, 1]
        source: pytest
        weight_in_reward: 0.2
      astra_evidence_and_decisions:
        range: [0, 1]
        source: pytest
        weight_in_reward: 0.2
    diagnostic_only:
      answer_found_elsewhere:
        range: [0, 1]
        source: script
        reward_contribution: none
  outputs:
    reward_text: /logs/verifier/reward.txt
    reward_json: /logs/verifier/reward.json
---

## verifier intent

This task no longer fits the `combine: weighted_sum` / independent-dimensions
shape the template assumes on its own, and the rubric block above says so
explicitly rather than inventing three peer weights that happen to reproduce
a number.

**`science_level` is one ordinal 0-3, not three weighted dimensions.**
`fit_correct` -> `systematics_covariance` -> `paper_reproduced` are strictly
nested: you cannot reach level 3 without level 2, or level 2 without level
1. That is a single ladder of scientific progress, not three independent
things needing relative importances nobody could actually justify (why would
finding the systematics covariance be worth more than a working fit but less
than a full reproduction, and by how much?). The old `analysis_executed`
dimension (a valid, non-trivial Hubble diagram PNG) is absorbed into level 1,
since a fit without a figure to show for it isn't yet a completed piece of
science at any level.

**`science_level`, `astra_spec_valid`, and `astra_evidence_and_decisions`
combine into `reward` as `0.6 * (science_level / 3) + 0.2 * astra_spec_valid
+ 0.2 * astra_evidence_and_decisions`, and each is still reported as its own
key.** This task is tier A of a three-tier ablation (no ASTRA / ASTRA named /
ASTRA named + plugin) — the instruction never says "ASTRA" at all, so the
two ASTRA flags measure whether an agent reaches for it unprompted (tier A)
or whether the plugin makes the difference (tier C), and score 0 for a
baseline agent doing perfect, unassisted science. Earlier revisions of this
task kept them out of the reward entirely on the reasoning that folding them
in would make tier A's number incomparable to tier C's. That measured
something real, but the reward is explicitly meant to measure instruction
following for now — deeper science-capability rubrics are a later
milestone — and both the science ladder and ASTRA activation are examples
of instructions the prompt actually gives (tier B/C's prompt does say "set
this up as an ASTRA analysis"), so both belong in the one number that
answers "did the agent do what was asked." Keeping each also reported
individually is what preserves the earlier objection's point: a reader can
still separate "did the science" from "used ASTRA" by looking at
`science_level` versus the two flags, without the combined `reward` hiding
that distinction.

`astra_spec_valid` checks that `astra.yaml` is schema- and
semantically-valid and declares a data input, a metric output, and a
downstream figure output, each with a recipe command.
`astra_evidence_and_decisions` checks that the paper's Omega_Lambda
constraint was verified as evidence AND that the spec's `decisions:` block
names both choices — the covariance decision with its systematics-inclusive
option selected, and the magnitude-treatment decision with its marginalized
option selected.

**The science rungs read a named output contract strictly, not a glob.** Both
instruction files tell the agent exactly where to put the answer, in wording
that must match `environment/project/contract.json` — the single source of
truth for the project root, the two result paths, and the two JSON key
names. That same file is baked into the image at
`/root/sn-cosmology/contract.json`, so `tests/_util.py`,
`solution/scripts/fit.py`, `solution/scripts/plot_hubble.py`, and
`solution/solve.sh` all read it rather than restating the paths or keys
independently; `check_contract_drift.py` (task root, not part of `test.sh` —
see its docstring for why) is the guard that the two instruction files still
match it. All three `science_level` pytest modules (`_util.py`'s
`read_named_best_fit()`) read only the contract's named file and keys — no
globbing, no key-name pattern matching. If the file is absent, unparseable,
or missing a key, `science_level` is 0, which is correct: the prompt asked
for it plainly, so "the answer exists somewhere in the agent's head or in
stdout" is a real failure worth catching, not something the verifier should
compensate for by searching harder. Level 3's value/uncertainty pairing is
automatically the same estimate, since both keys are read from the one named
file. The four tolerance windows themselves live in `tests/tolerances.json`,
kept out of the baked project deliberately — unlike the paths and keys, they
are not disclosed in the prompt, and baking them in would leak the scoring
thresholds to the agent.

The looser glob+pattern search this task used to score with
(`find_omega_lambda_estimates()` in `_util.py`) still exists, but purely as
the `answer_found_elsewhere` diagnostic (`check_answer_elsewhere.py`, run
directly by `test.sh`, not through pytest): it re-scans every JSON/YAML
under the project (excluding `data/` and the spec) for anything matching
those old key-pattern regexes, outside the named file. It never touches
`science_level` or `reward`. Its purpose is purely diagnostic — telling "the
agent couldn't do the physics" (`answer_found_elsewhere: 0`, `science_level:
0`) apart from "the agent did the physics but filed it somewhere else"
(`answer_found_elsewhere: 1`, `science_level: 0`) when reviewing failure
modes. The specific location(s) found, if any, are written to
`/logs/verifier/answer-elsewhere.txt` rather than into `reward.json`, since
`lightcone-bench`'s `summarize.py` only keeps numeric keys from that file.

ASTRA spec authoring is a different matter from the named output contract:
the agent chooses astra.yaml's own paths, decision IDs, and option IDs, so
`astra_spec_valid` and `astra_evidence_and_decisions` stay tolerant there —
pattern-matching option text for "systematic"/"statistical" and
"marginalize"/"fixed" rather than requiring specific IDs. What's checked
strictly for those two flags is the validation outcomes (`astra validate`
and `--verify-evidence` must both report full success) and that both
decisions are present with the right option selected as default.

Each level's pytest module checks only its own incremental condition — level
2's module does not re-check level 1's fit, level 3's does not re-check
level 2's uncertainty window — because `test.sh` only advances the ladder
while the previous rung already passed, enforcing the nesting structurally
rather than by re-testing or by weighting.
