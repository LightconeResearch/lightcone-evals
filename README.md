# lightcone-evals

Evaluation tasks of the Lightcone Research Stack.

This repo holds the **tasks** only. The runner infrastructure (CI workflow,
oracle gate, agent matrix, reporting, baselines) lives in `lightcone-bench`.

## Layout

```
template/        # copyable Harbor 1.4 task template (see template/README.md)
lightcone-cli/   # tasks targeting the lightcone-cli stack
  snae-end-to-end-local/   # estimate, materialize one boundary, plan oversized work
  snae-build/              # natural-language request + "Use lightcone-cli"
  snae-run-natural/        # same request without naming the tool
```

Tasks are grouped by the stack under test; one folder per task, in Harbor 1.4
split layout (`task.toml`, `instruction.md`, `environment/`, `solution/`,
`tests/`). Start a new task by copying `template/`.

All three SNAE tasks default to CLI `main`. The benchmark runner resolves that branch
once to a commit before image construction; pass `STACK_REF` (runner) or
`--build-arg LIGHTCONE_COMMIT=<sha>` (direct Docker build) to override. Direct
Docker builds with a mutable branch argument require a fresh build/cache refresh
to pick up branch changes.

[`snae-end-to-end-local` v2.0](lightcone-cli/snae-end-to-end-local/README.md)
uses the current `lc init` / `lc materialize` engine and the CLI's matching ASTRA
dependency. It retains the resource estimation, local execution and oversized
work classification scenario. Select `task=lightcone-cli/` to run all three
tasks, or select it alone. Regenerate its baseline after upgrading from v1.

The current pair is [`snae-run-natural` v0.2](lightcone-cli/snae-run-natural/README.md)
and [`snae-build` v0.3](lightcone-cli/snae-build/README.md). They have identical
environment files, scientific fixtures, oracle solutions and five-dimension
verifiers. Their prompts differ only by the opening sentence
"Use lightcone-cli for this task." Neither supplies commands, steps or a
reporting protocol. The natural prompt does not name Lightcone; the installed
tool and normal project evidence remain discoverable in both conditions.

To compare them in lightcone-bench, select
`task=lightcone-cli/snae-run-natural,lightcone-cli/snae-build` with
`use_skills=false`. Until merged, set `tasks_ref=codex/snae-execution-evals`
(or the exact task commit). Keep model, agent settings and CLI commit fixed,
run multiple attempts, and report the two task scores separately. The runner's
default selection remains snae-build, now the tool-named condition.

These conditions represent two plausible user behaviors, not a measured share
of users. The tasks evaluate use of the existing project's execution and
provenance workflow, not unrestricted scientific problem solving. Skills,
tool installation and entirely new projects are separate conditions.

The detailed command-driven snae-build v0.2 is retained in Git history at
`26d42f3`; it was an execution regression scenario, not a realistic user prompt.
Its seven-dimension scores are incompatible with the current pair. The previous
natural v0.1 also named Lightcone, so regenerate baselines for both tasks.

See [validation](validation/README.md) for the pair consistency check and oracle
and negative-test procedures.
