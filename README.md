# lightcone-evals

Evaluation tasks of the Lightcone Research Stack.

This repo holds the **tasks** only. The runner infrastructure (CI workflow,
oracle gate, agent matrix, reporting, baselines) lives in `lightcone-bench`.

## Layout

```
template/        # copyable Harbor 1.4 task template (see template/README.md)
lightcone-cli/   # tasks targeting the lightcone-cli stack
  snae-end-to-end-local/   # exam-like: estimate, run one boundary, classify (older lc pin)
  snae-build/              # execution lifecycle: selective builds, invalidation, recovery, clone reproduction
```

Tasks are grouped by the stack under test; one folder per task, in Harbor 1.4
split layout (`task.toml`, `instruction.md`, `environment/`, `solution/`,
`tests/`). Start a new task by copying `template/`.

`snae-build` defaults to CLI `main`. The benchmark runner resolves that branch
once to a commit before image construction; pass `STACK_REF` (runner) or
`--build-arg LIGHTCONE_COMMIT=<sha>` (direct Docker build) to override. Direct
Docker builds with a mutable branch argument require a fresh build/cache refresh
to pick up branch changes. The older end-to-end task retains its historical pin.

The v0.2 execution rubric is intentionally incompatible with v0.1 scores.
Regenerate benchmark baselines after adopting this task version.
