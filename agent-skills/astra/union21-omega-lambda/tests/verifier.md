---
document_version: '0.4'
verifier:
  name: union21-omega-lambda-verifier
  default_strategy: pytest
  strategies:
    pytest:
      type: script
      command: ./test.sh
  rubric:
    combine: tier_dependent_mean
    reward_formula:
      baseline: "mean(fit_and_figure, systematics_covariance, paper_reproduced)"
      astra: "mean(fit_and_figure, systematics_covariance, paper_reproduced, spec_valid, evidence_verified)"
    # Every dimension is 0/1, measured and reported on every tier; only the
    # reward formula is tier-dependent. The numeric windows live in
    # tests/tolerances.json and are not restated here.
    dimensions:
      fit_and_figure:
        source: pytest
        licensed_by: [instruction.md, instruction-astra.md]
      systematics_covariance:
        source: pytest
        licensed_by: [instruction.md, instruction-astra.md]
      paper_reproduced:
        source: pytest
        licensed_by: [instruction.md, instruction-astra.md]
      spec_valid:
        source: pytest
        licensed_by: [instruction-astra.md]
      evidence_verified:
        source: pytest
        licensed_by: [instruction-astra.md]
  outputs:
    reward_text: /logs/verifier/reward.txt
    reward_json: /logs/verifier/reward.json
---

## verifier intent

Five independent 0/1 dimensions. Two standing rules govern all of them: **the
verifier may only require what the prompt actually asks for**, and **call
other code's checks rather than re-implementing them**.

**The three science dimensions are independent, not a ladder.** They are
nested *in fact* — any run inside the paper windows is also inside the
fit-and-figure and systematics windows — but nothing enforces the nesting and
`test.sh` runs all three unconditionally. A run that reproduces the paper's
numbers without writing a figure scores `paper_reproduced=1`,
`fit_and_figure=0`; that is information about the run, not an inconsistency.

- `fit_and_figure` — `omega_lambda` in its window at the contracted path and
  key, AND a valid non-trivial Hubble-diagram PNG. A fit with no figure to
  show for it is not yet a completed piece of science.
- `systematics_covariance` — `omega_lambda_err` in its window. That window
  excludes both statistical-only cases (~0.013 fixed-M, ~0.020
  marginalized-M) and admits either magnitude treatment once the
  systematics-inclusive covariance is used (~0.030–0.041).
- `paper_reproduced` — `omega_lambda` and `omega_lambda_err` both in the
  paper windows, read from the one named file, which makes "the same
  estimate" structural rather than asserted.

**The two ASTRA dimensions are astra-tools verdicts.** Every ASTRA-side check
is a call into the pinned `astra-tools==0.2.17` CLI in the image, read from
its exit code; nothing is re-derived from parsed YAML.

- `spec_valid` — `astra validate <spec>` exits 0, plus exactly the prompt's
  three nouns ("an `astra.yaml` capturing the inputs, the outputs and the
  choices made along the way"): `inputs`, `outputs` and `decisions` each
  non-empty. Those three are asserted from the YAML only because astra-tools
  0.2.17 requires none of them; everything the CLI *does* enforce — schema
  validity, a decision's `default` resolving to one of its own options, that
  default not being excluded, `when`/`from` reference resolution — is carried
  by the exit code alone.
- `evidence_verified` — at least one evidence item citing Suzuki et al. 2012
  (by arXiv id or by the journal DOI, under `prior_insights` or under
  `findings`, which `astra validate` treats identically) verifies through
  `astra paper verify-quote`, whose exit code is the verdict (0 verified, 1
  not found, 2 not cached). A citation to the journal DOI
  `10.1088/0004-637X/746/1/85` is verified against `10.48550/arXiv.1105.3470`,
  the only DOI the image pre-caches.

Deliberately *not* `astra validate --verify-evidence`: that call is
all-or-nothing across every evidence item, so one extra Planck citation to a
paywalled DOI would sink an otherwise correct spec.

A previous check that a decision's `default` resolves to one of its own
options has been dropped as redundant: `astra validate` already errors on it
(`astra/validation/semantic.py`), and `spec_valid` already requires exit 0.
Its surviving half — that a decision exists at all — is the `decisions`
assertion above.

## tier mechanism

One verifier serves all three tiers of the ablation (no ASTRA / ASTRA named /
ASTRA named + plugin). It learns which prompt ran from `task.toml`'s
`[verifier.env] PROMPT_VARIANT`, which Harbor passes into the verifier as a
real environment variable. That key is written by the same step that swaps
the instruction file — `materialize.sh`'s `PROMPT_VARIANT` block in
`lightcone-bench`, or the local sweep driver — and the committed default is
`"baseline"`, which is correct for an unmaterialized task dir whose
`instruction.md` *is* the baseline prompt. `test.sh` echoes the variant it
saw into `reward.json`, so a mis-plumbed run is visible rather than merely
mis-scored.

The verifier never infers the tier from the agent's artifacts. "Does an
`astra.yaml` exist" would score the agent's behaviour in order to decide how
to score the agent's behaviour: tier A's rubric would flip the moment an
unprompted agent reached for ASTRA, which is precisely the signal the
ablation exists to measure.

**Reward is tier-dependent because the prompts are.** A prompt that never
mentions ASTRA cannot be scored on ASTRA flags, so `baseline` averages the
three science dimensions and `astra` averages all five. A weak spec can
therefore pull a tier-B/C run below an otherwise-identical tier-A run. That
is intended: scores are comparable *within* a prompt, never across prompts.
All five dimensions are still reported on every tier, so "did the science"
stays legible from "used ASTRA" — under tier A the two ASTRA flags carry
their real measured values (usually 0) while contributing nothing to reward.

## standing caveat on evidence verification in this environment

The image only pre-caches the arXiv preprint DOI. `10.1088/0004-637X/746/1/85`
(Suzuki's own journal DOI) and both Planck DOIs seen in practice
(`10.1051/0004-6361/201833910`, `10.1051/0004-6361/201321529`) are behind a
publisher paywall/CAPTCHA and genuinely unfetchable via `astra paper add` —
confirmed by trying them with live network access, not inferred. An agent
that cites the canonical published DOI over the arXiv preprint we happen to
pre-cache would fail to verify that citation through no fault of its own
reasoning; this is scoring our cache, not the agent, which is why the
journal DOI is remapped and why verification is scoped to "at least one"
rather than "all".

## what this verifier deliberately does not require

The rule is that the verifier may only require what the instruction file
actually asks for.

- Particular `type:` tokens on the declared inputs and outputs, and a figure
  output naming the metric output as an upstream dependency — both
  structural opinions the prompt never states.
- Recipe commands on any output — the prompt asks for inputs, outputs and
  choices, not executable provenance, and recipes are optional in the schema.
- Which particular scientific decisions are recorded (systematics
  covariance, marginalized magnitude) — that is the science dimensions'
  measurement; requiring specific ones inside `spec_valid` would measure the
  science twice and confound the ablation. Accepted cost: a spec carrying one
  trivial but well-formed decision passes that clause.
- Every citation verifying: only the required Suzuki claim has to verify, so
  an extra, unfetchable citation the agent chose to add cannot sink the flag.
- The non-selected option's prose: nothing reads a rejected option's text.
- The figure actually being two-panel, and the prompt's closing "tell me what
  you had to do to get there and where you still differ" narrative. Both
  instruction files ask for these and nothing scores them: decoding PNG row
  bands would be fragile complexity for a structural proxy, and the written
  account has no file the prompt names. Known gaps, stated here rather than
  papered over.

## the science dimensions read a named output contract strictly

Both instruction files tell the agent exactly where to put the answer, in
wording that must match `environment/project/contract.json` — the single
source of truth for the project root, the two result paths, and the two JSON
key names. That file is baked into the image at
`/root/sn-cosmology/contract.json`, so `tests/_util.py`,
`solution/scripts/fit.py`, `solution/scripts/plot_hubble.py`, and
`solution/solve.sh` all read it rather than restating paths or keys
independently; `check_contract_drift.py` (task root, not part of `test.sh` —
see its docstring for why) guards that the two instruction files still match
it.

`_util.read_named_best_fit()` reads only the contract's named file and keys —
no globbing, no key-name pattern matching. If the file is absent,
unparseable, or missing a key, the science dimensions are 0, which is
correct: the prompt asked for it plainly, so "the answer exists somewhere in
the agent's head or in stdout" is a real failure worth catching, not
something the verifier should compensate for by searching harder. The four
tolerance windows live in `tests/tolerances.json`, kept out of the baked
project deliberately — unlike the paths and keys, they are not disclosed in
the prompt, and baking them in would leak the scoring thresholds.

ASTRA spec authoring is a different matter: the agent chooses `astra.yaml`'s
own paths, decision IDs and option IDs, so `spec_valid` and
`evidence_verified` never require specific IDs, a particular dependency
shape, or particular decisions.
