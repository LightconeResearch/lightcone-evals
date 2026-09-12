---
document_version: '0.5'
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
      baseline: "mean(deliverables, omega_lambda_score, omega_lambda_err_score)"
      astra: "mean(deliverables, omega_lambda_score, omega_lambda_err_score, spec_valid, evidence_verified)"
    # Every dimension is measured and reported on every tier; only the reward
    # formula is tier-dependent. The reference values the two continuous
    # scores are measured against live in tests/reference.json.
    dimensions:
      deliverables:
        range: [0, 1]
        kind: binary
        source: pytest
        licensed_by: [union21-omega-lambda, union21-omega-lambda-astra]
      omega_lambda_score:
        range: [0, 1]
        kind: continuous
        source: score.py
        licensed_by: [union21-omega-lambda, union21-omega-lambda-astra]
      omega_lambda_err_score:
        range: [0, 1]
        kind: continuous
        source: score.py
        licensed_by: [union21-omega-lambda, union21-omega-lambda-astra]
      spec_valid:
        range: [0, 1]
        kind: binary
        source: pytest
        licensed_by: [union21-omega-lambda-astra]
      evidence_verified:
        range: [0, 1]
        kind: binary
        source: pytest
        licensed_by: [union21-omega-lambda-astra]
  outputs:
    reward_text: /logs/verifier/reward.txt
    reward_json: /logs/verifier/reward.json
    details_json: /logs/verifier/details.json
---

## the task

An agent is dropped into `/root/sn-cosmology` with the Union2.1 supernova compilation (Suzuki et al. 2012) — distance moduli, a statistics-only covariance matrix, and a systematics-inclusive one.
It is asked to fit a spatially flat ΛCDM model for the dark-energy density Ω_Λ, write the answer and its uncertainty to `results/best_fit.json` under the keys `omega_lambda` and `omega_lambda_err`, draw a Hubble diagram to `results/hubble_diagram.png`, and reproduce the paper's own published constraint.

Two things stand between a naive fit and the paper's number, and neither is stated in the prompt.
The obvious covariance file to reach for is the statistics-only one; the paper uses the systematics-inclusive one.
And the supernova absolute magnitude is a nuisance parameter that must be marginalized over rather than held fixed.
Each omission leaves Ω_Λ roughly right and its **uncertainty** far too small — which is why the uncertainty, not the central value, is where this task's difficulty actually lives.

The sibling task `union21-omega-lambda-astra` carries a prompt that additionally asks the agent to record the work as an `astra.yaml`: the inputs, the outputs, the choices made along the way, and the paper's constraint recorded as evidence.

## the five dimensions

One binary floor, two continuous science scores, two binary ASTRA flags.

| dimension | range | what it measures |
|---|---|---|
| `deliverables` | 0 or 1 | are the two named files there, readable, and numeric |
| `omega_lambda_score` | 0 to 1 | how close Ω_Λ is to the paper's value |
| `omega_lambda_err_score` | 0 to 1 | how close the reported uncertainty is to the paper's |
| `spec_valid` | 0 or 1 | `astra validate` passes and the spec has the prompt's three nouns |
| `evidence_verified` | 0 or 1 | a Suzuki citation verifies through `astra paper verify-quote` |

Two standing rules govern all five: **the verifier may only require what the prompt actually asks for**, and **call other code's checks rather than re-implementing them**.

### the science is scored as a distance, not as a window

The two numbers this task produces are numbers, and what is interesting about a run is *how far off* it was.
A pass/fail window on σ scores a near-miss at 0.024 exactly the same as a 0.0005 that is a different kind of error entirely, and that distinction is most of the signal the task exists to produce.

One thing can reasonably be binary — does the best-fit file exist, does the PNG exist — and that is the floor.
Everything above the floor is a distance, scored as a distance.

### `deliverables` — the binary floor

1 if and only if:

- the named `results/best_fit.json` exists, parses as a JSON object, and carries both `omega_lambda` and `omega_lambda_err` as finite numbers (not strings, not booleans, not null, and not `NaN` or `Infinity` — which Python's JSON reader accepts and no conforming one does), **and**
- the named `results/hubble_diagram.png` exists, is larger than 10 kB, starts with the PNG magic bytes, and decodes to a non-empty image array.

The 10 kB floor and the decode are there to reject a zero-byte placeholder or a truncated write, not to judge the figure's content.
The file is read strictly at the contracted path and keys — no globbing, no key-name pattern matching — because both prompts state that contract in plain prose.
"The answer exists somewhere in the agent's head or in stdout" is a real failure worth catching, not something the verifier should compensate for by searching harder.

### `omega_lambda_score` — a Gaussian in Ω_Λ

```
omega_lambda_score = exp(-0.5 * ((omega_lambda - 0.705) / 0.0415)^2)
```

The reference is Suzuki et al. 2012's SN-only flat-ΛCDM result, Ω_Λ = 0.705 (+0.040, −0.043), symmetrised to a single σ_ref = 0.0415.
The score is a Gaussian whose width is *the paper's own uncertainty*, so the natural reading is "how many paper-sigmas away is this answer".

| Ω_Λ | score | |
|---|---|---|
| 0.705 | 1.00 | the published value |
| 0.712 | 0.99 | |
| 0.690 | 0.94 | |
| 0.735 | 0.77 | |
| 0.705 ± 0.0415 | 0.61 | one paper-σ off |
| 0.705 ± 0.083 | 0.14 | two paper-σ off |

A missing file, a missing key, or a non-numeric value scores 0.

### `omega_lambda_err_score` — a Gaussian in log σ

```
omega_lambda_err_score = exp(-0.5 * (ln(omega_lambda_err / 0.0415) / ln(1.4))^2)
```

An uncertainty is a *scale*, not a location, so the distance is measured in the logarithm.
Being a factor of two too small and a factor of two too large are the same size of mistake, and a gap of 0.02 means something entirely different at σ = 0.04 than at σ = 0.4.
The width is one factor of 1.4: a σ that is 1.4× too small or 1.4× too large scores exp(−1/2) = 0.61.

The worked reference points are the four ways this analysis can actually come out.

| what the agent did | σ | score |
|---|---|---|
| statistics-only covariance, magnitude held fixed | ≈0.013 | 0.00 |
| statistics-only covariance, magnitude marginalized | ≈0.020 | 0.10 |
| systematics covariance, magnitude held fixed | ≈0.030 | 0.63 |
| systematics covariance, magnitude marginalized | ≈0.041 | 1.00 |

That ladder is the point of the score.
Finding neither seeded defect scores ~0; finding one scores roughly a half; finding both scores ~1.
A missing, non-numeric, or non-positive σ scores 0 — a non-positive number has no logarithm and is not an uncertainty.

### `spec_valid` and `evidence_verified` — astra-tools verdicts

Both binary, because the tools they call are.
Every ASTRA-side check is a call into the pinned `astra-tools==0.2.17` CLI in the image, read from its exit code; nothing is re-derived from parsed YAML.

- `spec_valid` — `astra validate <spec>` exits 0, plus exactly the prompt's three nouns ("an `astra.yaml` capturing the inputs, the outputs and the choices made along the way"): `inputs`, `outputs` and `decisions` each non-empty.
  Those three are asserted from the YAML only because astra-tools 0.2.17 requires none of them; everything the CLI *does* enforce — schema validity, a decision's `default` resolving to one of its own options, that default not being excluded, `when`/`from` reference resolution — is carried by the exit code alone.
- `evidence_verified` — at least one evidence item citing Suzuki et al. 2012 (by arXiv id or by the journal DOI, under `prior_insights` or under `findings`, which `astra validate` treats identically) verifies through `astra paper verify-quote`, whose exit code is the verdict (0 verified, 1 not found, 2 not cached).
  A citation to the journal DOI `10.1088/0004-637X/746/1/85` is verified against `10.48550/arXiv.1105.3470`, the only DOI the image pre-caches.

Deliberately *not* `astra validate --verify-evidence`: that call is all-or-nothing across every evidence item, so one extra Planck citation to a paywalled DOI would sink an otherwise correct spec.

## reward

```
baseline (union21-omega-lambda)        reward = mean(deliverables, omega_lambda_score, omega_lambda_err_score)
astra    (union21-omega-lambda-astra)  reward = mean(the same three, spec_valid, evidence_verified)
```

Rounded to two decimals.
All five dimensions are reported on every tier, so "did the science" stays legible from "used ASTRA" — under the baseline tier the two ASTRA flags carry their real measured values (usually 0) while contributing nothing to reward.

**Reward is tier-dependent because the prompts are.**
A prompt that never mentions ASTRA cannot be scored on ASTRA flags.
A weak spec can therefore pull a tier-B/C run below an otherwise-identical tier-A run.
That is intended: scores are comparable *within* a prompt, never across prompts.

## the two output files, and why there are two

Harbor 0.22.0 parses `/logs/verifier/reward.json` as a flat map of name → number (`VerifierResult.rewards: dict[str, float | int]`) and raises a pydantic `ValidationError` on any string or null value.
A single string in that map is enough to sink a trial: one written with `"prompt_variant": "astra"` recorded a perfectly good reward of 1.00 in `reward.json` alongside an `exception_info` in `result.json` saying `unable to parse string as an integer, input_value='astra'`.

So the verifier writes two files.

`/logs/verifier/reward.json` — numbers only, exactly these six keys:

```json
{"reward": 1.0, "deliverables": 1, "omega_lambda_score": 1.0,
 "omega_lambda_err_score": 0.9994, "spec_valid": 1, "evidence_verified": 1}
```

`/logs/verifier/details.json` — everything non-numeric or contextual, collected by Harbor as an ordinary verifier log:

```json
{"prompt_variant": "astra", "omega_lambda": 0.7047, "omega_lambda_err": 0.0412,
 "omega_lambda_ref": 0.705, "omega_lambda_err_ref": 0.0415}
```

`omega_lambda` and `omega_lambda_err` in `details.json` are `null` when the agent produced no readable value — which is exactly the case `reward.json` cannot express, and the reason the split is not merely cosmetic.

## tier mechanism

One verifier serves all three tiers of the ablation (no ASTRA / ASTRA named / ASTRA named + plugin).
It learns which prompt ran from `task.toml`'s `[verifier.env] PROMPT_VARIANT`, which Harbor passes into the verifier as a real environment variable.
Each task states its own variant there: `union21-omega-lambda` states `"baseline"`, `union21-omega-lambda-astra` states `"astra"`.
Nothing downstream selects the variant, because the task a run points at already fixes it.
An unrecognised value is a hard error rather than a silently-chosen formula, and `details.json` echoes the variant the verifier saw, so a mis-plumbed run is visible rather than merely mis-scored.

The verifier never infers the tier from the agent's artifacts.
"Does an `astra.yaml` exist" would score the agent's behaviour in order to decide how to score the agent's behaviour: tier A's rubric would flip the moment an unprompted agent reached for ASTRA, which is precisely the signal the ablation exists to measure.

## the continuous scores are not pytest tests

A pytest run is pass or fail — 0 or 1.
A continuous score cannot be a pytest verdict without quantising it back into a window.
So `tests/score.py` is a plain module that reads the named `best_fit.json` through `_util` and prints its two scores as JSON on stdout; `test.sh` runs it and folds the result into both output files.
`test_science.py` keeps only `test_deliverables`, which genuinely is binary.

## standing caveat on evidence verification in this environment

The image only pre-caches the arXiv preprint DOI.
`10.1088/0004-637X/746/1/85` (Suzuki's own journal DOI) and both Planck DOIs seen in practice (`10.1051/0004-6361/201833910`, `10.1051/0004-6361/201321529`) are behind a publisher paywall/CAPTCHA and genuinely unfetchable via `astra paper add` — confirmed by trying them with live network access, not inferred.
An agent that cites the canonical published DOI over the arXiv preprint we happen to pre-cache would fail to verify that citation through no fault of its own reasoning; this is scoring our cache, not the agent, which is why the journal DOI is remapped and why verification is scoped to "at least one" rather than "all".

The evidence item's `version` field is not forwarded to `verify-quote` either.
The image caches one copy of the paper, and astra-tools keys a versioned lookup separately, so a legitimate `version: 1` citation would report "Paper not in cache" against that copy.
That would again score the cache rather than the agent.

## deliberate omissions

The rule is that the verifier may only require what the instruction file actually asks for.

- Particular `type:` tokens on the declared inputs and outputs, and a figure output naming the metric output as an upstream dependency — both structural opinions the prompt never states.
- Recipe commands on any output — the prompt asks for inputs, outputs and choices, not executable provenance, and recipes are optional in the schema.
- Which particular scientific decisions are recorded (systematics covariance, marginalized magnitude) — that is the continuous scores' measurement; requiring specific ones inside `spec_valid` would measure the science twice and confound the ablation. Accepted cost: a spec carrying one trivial but well-formed decision passes that clause.
- Every citation verifying: only the required Suzuki claim has to verify, so an extra, unfetchable citation the agent chose to add cannot sink the flag.
- The non-selected option's prose: nothing reads a rejected option's text.
- The figure actually being two-panel, and the prompt's closing "tell me what you had to do to get there and where you still differ" narrative. Both instruction files ask for these and nothing scores them: decoding PNG row bands would be fragile complexity for a structural proxy, and the written account has no file the prompt names. Known gaps, stated here rather than papered over.

## the named output contract

Both instruction files tell the agent exactly where to put the answer, in wording that must match `environment/project/contract.json` — the single source of truth for the project root, the two result paths, and the two JSON key names.
That file is baked into the image at `/root/sn-cosmology/contract.json`, so `tests/_util.py`, `solution/scripts/fit.py`, `solution/scripts/plot_hubble.py`, and `solution/solve.sh` all read it rather than restating paths or keys independently; `check_contract_drift.py` (task root, not part of `test.sh` — see its docstring for why) guards that the two instruction files still match it.

`tests/reference.json` holds the other half — Ω_Λ = 0.705, σ_ref = 0.0415, and the log-width 1.4 — and is deliberately kept out of the baked project.
Unlike the paths and keys, these are not disclosed in the prompt: baking the paper's answer into the agent's working directory would hand over the thing the task exists to make it derive.

ASTRA spec authoring is a different matter: the agent chooses `astra.yaml`'s own paths, decision IDs and option IDs, so `spec_valid` and `evidence_verified` never require specific IDs, a particular dependency shape, or particular decisions.
