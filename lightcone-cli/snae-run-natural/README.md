# snae-run-natural

The natural-language condition: the user describes the required work without
naming Lightcone. The agent must discover the existing project workflow.

The two tasks share byte-identical environment files, scientific fixtures,
reference solutions and verifiers. The only instruction difference is the prefix
"Use lightcone-cli for this task." Neither prompt supplies commands, flags,
tutorials, troubleshooting steps, a skill-loading request, report schemas or
checkpoint protocols. Native help, installed documentation, project sources and
the previous failure's actual log remain discoverable in both conditions.

## Work to complete

| Project | Starting state | Requested outcome |
|---|---|---|
| new-analysis | Complete scientific source; dependencies not declared | Only the Hubble diagram and required fit |
| updated-analysis | All products built under the previous uncertainty model | Update the results; reuse the independent catalog summary |
| interrupted-analysis | Corrected measurement; independent output succeeded; fit update failed | Repair execution, finish the update, preserve data and past results |

A separate reproduced-analysis repository and publication metadata for
updated-analysis complete the handoff. The scientific scripts are supplied so
the work centers on execution. The grader reads final project state, output
bytes and ordinary execution history, without requiring special reports or tags.
The same five outcome dimensions have equal weight in both tasks.

Agents run as the `agent` user and own all prepared repositories, including annex
objects. Verification runs as root. Image-owned references are inaccessible to
the ordinary agent; preparation code is removed after setup. The workspace has
no injected skills, plugins, hooks, AGENTS.md or task-specific tutorials.

## Comparison

In lightcone-bench select both tasks with
`task=lightcone-cli/snae-run-natural,lightcone-cli/snae-build` and
`use_skills=false`. Until merged, set `tasks_ref=codex/snae-execution-evals`
(or its commit). The CLI defaults to main, resolved to one immutable commit for
both conditions; an explicit `stack_ref` overrides it. The default single task
remains snae-build, the tool-named condition.

Use the same model and agent settings, run multiple attempts, and compare the
two task scores separately. This measures the effect of explicitly naming the
tool in this prepared-project setting; it does not establish what fraction of
users each condition represents. Enabling skills is another experimental factor.
The natural condition does not eliminate model prior knowledge or project clues.

Earlier snae-build v0.2 had detailed instructions, different initial states and
seven score dimensions. It remains available at task commit `26d42f3` as a
historical regression scenario. Its scores are not comparable with the current
pair. Natural v0.1 also named Lightcone; regenerate both baselines.

## Validation

See [validation instructions](../../validation/README.md) for the pair consistency
check, Harbor oracle and six corrupted-outcome checks. Both oracles must score
1.0 across all five dimensions with zero errors. The pair check guards against
accidental divergence in prompts, environments, solutions, verifiers or runtime
settings.
