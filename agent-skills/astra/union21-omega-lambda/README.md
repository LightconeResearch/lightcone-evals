# union21-omega-lambda

The baseline tier of a three-tier ASTRA-adoption ablation:

| tier | task | skill installed | measures |
|---|---|---|---|
| A | `union21-omega-lambda` | no | does the agent do good science at all — the prompt never mentions ASTRA |
| B | `union21-omega-lambda-astra` | no | does naming ASTRA without the skill help, hurt, or do nothing |
| C | `union21-omega-lambda-astra` | yes | does the plugin make the difference |

Tiers A and B are sibling task directories, each with its own `instruction.md` and its own `task.toml`.
They share one environment, one oracle and one verifier: the sibling's `environment/`, `tests/` and `solution/` are relative symlinks into this directory, so the ~7 MB `data/` directory is not duplicated.
Tier C is tier B run with the skill installed (`harbor run -p agent-skills/astra/union21-omega-lambda-astra --skill <astra skill dir>`).

The sibling's prompt names ASTRA and says the choices belong in the spec, but deliberately does not teach the format — no `prior_insights`, `decisions:`, recipe syntax, output types, or CLI commands.
Teaching the format is the skill's job; if the prompt taught it too, tiers B and C would converge and the ablation would measure nothing.

The verifier is one script, one rubric and one formula for all three tiers.
It scores five dimensions — one binary floor, two continuous science scores, and two binary ASTRA flags — and reports all five on every tier, so "did the science" stays legible from "used ASTRA".

| dimension | range | what it measures |
|---|---|---|
| `deliverables` | 0 or 1 | the named `best_fit.json` has both numeric values AND the named PNG exists and decodes |
| `omega_lambda_score` | 0 to 1 | `exp(-0.5 * ((omega_lambda - 0.705) / 0.0415)^2)` |
| `omega_lambda_err_score` | 0 to 1 | `exp(-0.5 * (ln(omega_lambda_err / 0.0415) / ln(1.4))^2)` |
| `spec_valid` | 0 or 1 | `astra validate` passes and the spec has inputs, outputs and decisions |
| `evidence_verified` | 0 or 1 | a Suzuki citation verifies through `astra paper verify-quote` |

The two references are Suzuki et al. 2012's SN-only flat-LCDM constraint, Omega_Lambda = 0.705 (+0.040, -0.043), symmetrised to a single sigma of 0.0415.
The central-value score is a Gaussian whose width is the paper's own uncertainty (1.00 on the published value, 0.61 one paper-sigma off).
The uncertainty score is a Gaussian in *log* sigma, because an uncertainty is a scale: a factor of 1.4 too small and a factor of 1.4 too large are the same size of mistake, and both score 0.61.
Both scores require a finite number; a missing, non-numeric, `NaN` or (for sigma) non-positive value scores 0.

That second score is where this task's difficulty lives, because each of the two seeded defects leaves Omega_Lambda roughly right and its uncertainty far too small:

| what the run did | sigma | score |
|---|---|---|
| statistics-only covariance, magnitude fixed | ~0.013 | 0.00 |
| statistics-only covariance, magnitude marginalized | ~0.020 | 0.10 |
| systematics covariance, magnitude fixed | ~0.030 | 0.63 |
| systematics covariance, magnitude marginalized (the paper) | ~0.041 | 1.00 |

The reward is the mean of all five, for every task:

```
reward = mean(deliverables, omega_lambda_score, omega_lambda_err_score, spec_valid, evidence_verified)
```

This task's prompt never asks for ASTRA, so `spec_valid` and `evidence_verified` are measured 0 here and **its reward is capped at 0.60 by construction**.
That cap is the size of the gap adopting ASTRA is being asked to close.
The two flags still carry their real measured values, so an unprompted agent that reaches for ASTRA anyway — the activation measurement the ablation exists to produce — shows up as exactly that.
Compare rewards *within* a task, never across tasks.

The verifier writes two files, not one.
Harbor 0.22.0 parses `/logs/verifier/reward.json` as a flat map of name -> number and raises a pydantic `ValidationError` on any string or null value, so `reward.json` carries numbers only.
Everything else — which prompt ran, the raw fitted values, the references — goes to a sibling `details.json`.

Because the formula is fixed, the verifier never has to learn which prompt ran, and in particular never infers it from the agent's artifacts — a rubric that flipped on "does an `astra.yaml` exist" would score the agent's behaviour in order to decide how to score the agent's behaviour.
See `tests/verifier.md` for the full rubric rationale.

## Re-scoring finished trials

`scripts/rescore.sh` re-runs the current verifier against trials that already finished, without re-running the agent.
A Harbor trial dir keeps the agent's work products under `artifacts/` (`astra.yaml`, `best_fit.json`, `hubble_diagram.png` — collected by `task.toml`'s `artifacts` block), and that is everything the verifier reads.

```
scripts/rescore.sh jobs/sweep-sonnet-C/sweep-sonnet-C/BC__WA2D3CQ
find jobs -maxdepth 3 -mindepth 3 -type d -print0 | xargs -0 scripts/rescore.sh
```

Results land in `<trial_dir>/verifier-v3/`; nothing already in the trial dir is touched, so Harbor's own `verifier/` collection from the live run stays as it was.
One summary line per trial goes to stdout.
Every trial is graded by the same formula, so no tier has to be supplied; the trial-name prefix (`A__*`, `BC__*`) only labels the summary line.
It needs the task image locally (`UNION21_IMAGE`, default `union21-env:v2`); build it with `docker build -t union21-env:v2 environment/`.

## Single sources of truth

`environment/project/contract.json` governs the project root, the two named result paths, and the two JSON key names.
`tests/reference.json` governs the two published reference values and the log-width factor, and is deliberately kept out of the image, since baking the paper's answer into the agent's working directory would hand over the thing the task exists to make it derive.
Run `python3 check_contract_drift.py` after editing either task's `instruction.md`, `contract.json`, or either `task.toml`; it checks both tasks.
See that script's docstring for why it is not part of `test.sh`.
