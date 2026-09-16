# snae-run-natural

An execution-discovery task with an outcome-only natural-language prompt.
`instruction.md` contains no command names, flags, tutorials, suggested
troubleshooting steps, skill-loading request, report schema, or checkpoint
protocol. It names Lightcone because that is the tool being evaluated.
Native tool help, installed documentation, project source and the previous
failure's actual log remain discoverable; they are not injected as instructions.

The image supplies three independent projects:

| Project | Starting state | Requested outcome |
|---|---|---|
| new-analysis | Complete scientific source; dependencies not declared | Only the Hubble diagram and required fit |
| updated-analysis | All products built under the previous uncertainty model | Results updated for the already changed uncertainty model; independent output reused |
| interrupted-analysis | A corrected measurement; independent output succeeded; fit update failed | Repair execution, finish the update, retain corrected inputs and past results |

A separate reproduced-analysis repository and publication metadata for
updated-analysis complete the handoff. The scientific code is supplied so the
agent's work centers on discovering and operating the execution tool.

The task explicitly runs agents as the `agent` user, which owns all prepared
repositories (including their existing annex objects); verification runs as root.

Starting states make the outcomes observable without telling the agent how to
record its actions. Image-owned references are not available to the ordinary
agent. Image setup is removed after preparation; there are no baked-in skills,
plugins, hooks, AGENTS.md, or task-specific tutorials in the workspace.

## Running

From this repository, validate without a model:

```bash
uvx --from harbor==0.22.0 harbor run \
  -p lightcone-cli/snae-run-natural -a oracle -e docker \
  -o /tmp/snae-natural-oracle --job-name oracle -q -y
```

In lightcone-bench select `task=lightcone-cli/snae-run-natural` and leave
`use_skills=false` for the natural baseline. Before this branch is merged, set
`tasks_ref=codex/snae-execution-evals` (or its commit). The CLI still defaults to
main, resolved to one immutable commit per benchmark run. An explicit stack_ref
overrides it.

Enabling skills is a different experimental condition. The existing snae-build
remains the guided lifecycle task and the runner default. The two tasks differ
in their starting states and scoring, so raw score differences are not a
controlled estimate of the effect of guidance. Compare repeated runs with
fixed versions and agent settings within snae-run-natural.

## Validation

The oracle must score 1.0 across all five dimensions. The grader requires no
agent-created reports or tags. `validation/check_snae_natural_mutations.py`
can be mounted at `/validation` in a completed oracle container (with task tests
at `/tests`) to ensure incorrect outcomes lose credit.
