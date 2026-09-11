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
        # The numeric windows live in tests/tolerances.json; they are not
        # restated here.
        levels:
          0: "no working fit"
          1: "recorded Omega_Lambda in the level-1 window AND a valid non-trivial Hubble diagram PNG"
          2: "level 1, AND recorded a 1-sigma in the level-2 window (systematics covariance found)"
          3: "level 2, AND recorded Omega_Lambda and 1-sigma in the level-3 windows on the same estimate (paper reproduced)"
    astra_flags:
      astra_spec_valid:
        range: [0, 1]
        source: pytest
        weight_in_reward: 0.2
      astra_evidence_and_decisions:
        range: [0, 1]
        source: pytest
        weight_in_reward: 0.2
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

`astra_spec_valid` checks that `astra.yaml` passes `astra validate` and
declares a data input, a metric output, and a figure output — nothing more.
The verdict comes from the CLI's exit code, not from re-reading its report.

`astra_evidence_and_decisions` checks two things the prompt does ask for:
that at least one evidence quote citing Suzuki et al. 2012 (by arXiv id or
by the journal DOI, under `prior_insights` or under `findings` — `astra
validate` verifies both identically) verifies against the cached paper, and
that the spec records at least one decision whose `default` resolves to one
of its own options. *Which* decisions the agent recorded is `science_level`'s
question; requiring particular ones here would measure the science twice and
confound the ablation the task exists to run. Accepted cost: a spec carrying one
trivial but well-formed decision now passes that half of the flag.

**Deliberate boundary: verdicts come from the CLI, spec *content* is read
from YAML.** `astra validate` decides validity and `astra paper verify-quote`
decides whether a quote is in the paper, so those two are invoked and their
exit codes read rather than re-derived. Everything else this verifier needs
to know about the spec (which output types are declared, whether a decision
selects one of its options) is read straight from the YAML, because
astra-tools 0.2.17 exposes no structured spec dump — `astra info --json`
returns a rendered text blob.

**Standing caveat on evidence verification in this environment.** The
image only pre-caches the arXiv preprint DOI. `10.1088/0004-637X/746/1/85`
(Suzuki's own journal DOI) and both Planck DOIs seen in practice
(`10.1051/0004-6361/201833910`, `10.1051/0004-6361/201321529`) are behind a
publisher paywall/CAPTCHA and genuinely unfetchable via `astra paper add` —
confirmed by trying them with live network access, not inferred. An agent
that cites the canonical published DOI over the arXiv preprint we happen to
pre-cache will fail to verify that citation through no fault of its own
reasoning; this is scoring our cache, not the agent, which is exactly why
verification is scoped to "at least one" rather than "all."

**What this verifier deliberately does not require.** Each of these was
either a real scoring bug or an obvious temptation; the rule is that the
verifier may only require what the instruction file actually asks for.

- A figure output naming the metric output as an upstream dependency — a
  structural opinion the prompt never states; `test_astra_spec_valid.py`
  carries the comment that keeps it out.
- Recipe commands on the metric or figure outputs — the prompt asks for
  inputs, outputs and choices, not executable provenance, and recipes are
  optional in the schema.
- Which particular scientific decisions are recorded (systematics
  covariance, marginalized magnitude) — that is `science_level`'s
  measurement, not this flag's.
- Every citation verifying: only the required Suzuki claim has to verify, so
  an extra, unfetchable citation the agent chose to add cannot sink the flag.
- The non-selected option's prose: an earlier matcher excluded a decision
  whose statistics-only option was correctly described as "ignoring
  systematic uncertainties". Nothing now reads a rejected option's text.
- The figure actually being two-panel, and the prompt's closing "tell me
  what you had to do to get there and where you still differ" narrative.
  Both instruction files ask for these and nothing scores them: decoding PNG
  row bands would be fragile complexity for a structural proxy, and the
  written account has no file the prompt names. Known gaps, stated here
  rather than papered over.

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

ASTRA spec authoring is a different matter from the named output contract:
the agent chooses astra.yaml's own paths, decision IDs, and option IDs, so
`astra_spec_valid` and `astra_evidence_and_decisions` never require specific
IDs, a particular output-to-output dependency shape, or particular decisions.

Each level's pytest module checks only its own incremental condition — level
2's module does not re-check level 1's fit, level 3's does not re-check
level 2's uncertainty window — because `test.sh` only advances the ladder
while the previous rung already passed, enforcing the nesting structurally
rather than by re-testing or by weighting.
