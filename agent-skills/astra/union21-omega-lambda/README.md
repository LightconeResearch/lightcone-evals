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
exists to produce, not a bug to fix. `science_level` (and therefore
`reward = science_level / 3`) is the number that is comparable across all
three tiers regardless of ASTRA use; see `tests/verifier.md` for the full
rubric rationale.

## Single sources of truth

The output contract — the project root, the named result paths, and the two
JSON key names both instruction files state in prose — is authoritative in
`environment/project/contract.json`, not restated as independent literals
anywhere else. It is baked into the image at `/root/sn-cosmology/contract.json`
(safe for the agent to see: the prompt already discloses all of it), and
`tests/_util.py`, `solution/scripts/fit.py`, `solution/scripts/plot_hubble.py`,
and `solution/solve.sh` all read it rather than hardcoding the paths or keys.

The four `science_level` tolerance windows are authoritative in
`tests/tolerances.json` — deliberately *not* baked into the project, since
exposing the scoring thresholds to the agent would leak what the ablation is
measuring against. `tests/verifier.md` restates them in prose for
readability; `tests/tolerances.json` and `environment/project/contract.json`
are the values that actually govern scoring if the two ever disagree.

`instruction.md` and `instruction-astra.md` are literal prose an agent
reads, so they can't import `contract.json` — run `check_contract_drift.py`
after editing either instruction file or the contract to confirm they still
agree. That script can't run inside a Harbor container (see its own
docstring for why) and isn't part of `test.sh`; it's a task-authoring guard,
not a scored dimension, and never affects `science_level`, `reward`, or the
ASTRA flags.
