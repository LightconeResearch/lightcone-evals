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

The verifier is identical across all three tiers. `astra_spec_valid` and
`astra_evidence_and_decisions` legitimately score 0 for a tier-A (or a
low-effort tier-B) run — that is the activation measurement the ablation
exists to produce, not a bug to fix. `reward = 0.6 * (science_level / 3) +
0.2 * astra_spec_valid + 0.2 * astra_evidence_and_decisions`: the reward
measures instruction-following for now (both the science ladder and ASTRA
activation are things the prompt asks for), while `science_level` and the
two ASTRA flags are each still reported individually so "did the science"
stays legible from "used ASTRA" even though they combine into one score;
see `tests/verifier.md` for the full rubric rationale.

## Single sources of truth

`environment/project/contract.json` governs the project root, the two named
result paths, and the two JSON key names; `tests/tolerances.json` governs the
four `science_level` windows and is deliberately kept out of the image, since
baking the scoring thresholds into the project would leak them to the agent.
Run `python3 check_contract_drift.py` after editing an instruction file,
`contract.json`, or `task.toml`. See that script's docstring for why it is not part of `test.sh`.
