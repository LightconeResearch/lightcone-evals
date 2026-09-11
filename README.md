# lightcone-evals

Evaluation tasks of the Lightcone Research Stack.

This repo holds the **tasks** only. The runner infrastructure (CI workflow,
oracle gate, agent matrix, reporting, baselines) lives in `lightcone-bench`.

## Layout

```
template/        # copyable Harbor 1.4 task template (see template/README.md)
lightcone-cli/   # tasks targeting the lightcone-cli stack
  snae-end-to-end-local/   # exam-like: estimate, run one boundary, classify (older lc pin)
  snae-build/              # naive-usage: build a seeded spec end to end (lightcone-cli's own eval, ported)
```

Tasks are grouped by the stack under test; one folder per task, in Harbor 1.4
split layout (`task.toml`, `instruction.md`, `environment/`, `solution/`,
`tests/`). Start a new task by copying `template/`.
