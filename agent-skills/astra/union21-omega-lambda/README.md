# union21-omega-lambda

One environment, one oracle, one verifier — two instruction files for a
three-tier ASTRA-adoption ablation:

| tier | instruction file | skill installed | measures |
|---|---|---|---|
| A | `instruction.md` | no | does the agent do good science at all — never mentions ASTRA |
| B | `instruction-astra.md` | no | does naming ASTRA without the skill help, hurt, or do nothing |
| C | `instruction-astra.md` | yes | does the plugin make the difference |

B and C are the same prompt; only `WITH_SKILLS` (in `lightcone-bench`'s
`materialize.sh`) differs between them, which is why this is two instruction
files rather than two tasks — duplicating the ~7 MB `data/` directory, the
oracle, and the verifier to vary one markdown file would be the wrong axis to
fork on. Which instruction file a given run uses is selected by
`materialize.sh`'s `PROMPT_VARIANT` env var (see that script's header comment
in `lightcone-bench`).

`instruction-astra.md` names ASTRA and says the choices belong in the spec,
but deliberately does not teach the format — no `prior_insights`,
`decisions:`, recipe syntax, output types, or CLI commands. Teaching the
format is the skill's job; if the prompt taught it too, tiers B and C would
converge and the ablation would measure nothing.

The verifier is one script for all three tiers. It scores five independent
0/1 dimensions — `fit_and_figure`, `systematics_covariance`,
`paper_reproduced`, `spec_valid`, `evidence_verified` — and reports all five
on every tier, so "did the science" stays legible from "used ASTRA".

Only the reward is tier-dependent, because the prompts are:

```
baseline (instruction.md)        reward = mean(fit_and_figure, systematics_covariance, paper_reproduced)
astra    (instruction-astra.md)  reward = mean(the same three, spec_valid, evidence_verified)
```

A prompt that never mentions ASTRA cannot be scored on ASTRA flags; under
tier A those two flags carry their real measured values (usually 0 — that is
the activation measurement the ablation exists to produce) while contributing
nothing to reward. A weak spec can pull a tier-B/C run below an
otherwise-identical tier-A run: rewards are comparable *within* a prompt,
never across prompts.

The verifier learns which prompt ran from `task.toml`'s `[verifier.env]
PROMPT_VARIANT`, never from the agent's artifacts. Whoever swaps the
instruction file must also write that key — `materialize.sh`'s
`PROMPT_VARIANT` block in `lightcone-bench` does, and so must any local sweep
driver that copies the task dir itself. The committed default is `"baseline"`,
correct for an unmaterialized task dir. See `tests/verifier.md` for the full
rubric rationale.

## Single sources of truth

`environment/project/contract.json` governs the project root, the two named
result paths, and the two JSON key names; `tests/tolerances.json` governs the
four science-dimension windows and is deliberately kept out of the image, since
baking the scoring thresholds into the project would leak them to the agent.
Run `python3 check_contract_drift.py` after editing an instruction file,
`contract.json`, or `task.toml`. See that script's docstring for why it is not part of `test.sh`.
