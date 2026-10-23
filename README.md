# lightcone-evals

Evaluation tasks of the Lightcone Research Stack.

This repo holds the tasks and the reusable eval workflow that runs them in
the repositories under test (`.github/workflows/eval.yml`). lightcone-bench
remains the place for cross-model benchmark runs.

## Layout

```
template/        # copyable Harbor 1.4 task template (see template/README.md)
lightcone-cli/   # tasks targeting the lightcone-cli stack
  snae-end-to-end-local/   # exam-like: estimate, run one boundary, classify (older lc pin)
  snae-build/              # naive-usage: build a seeded spec end to end (lightcone-cli's own eval, ported)
```

Tasks are grouped by the stack under test; one folder per task, in Harbor 1.4
split layout (`task.toml`, `instruction.md`, `environment/`, `solution/`,
`tests/`). Start a new task by copying `template/`. A task may also carry a
`rubric.toml` beside `task.toml`: the criteria `harbor analyze` judges its
trials by.

## The eval workflow

`.github/workflows/eval.yml` is called by lightcone-cli and agent-skills on
their PRs and on main. Each caller passes its own commit for the side under
test (`stack_ref` for lightcone-cli, `skills` for agent-skills) and its own
secrets through `secrets: inherit`; this repository's secrets never reach a
caller. The header comment holds both callers.

Per leg (one Harbor agent and model), the workflow pins the task image to the
lightcone-cli commit, requires the oracle to score 1.0, and runs the agent with
the skills installed through `--skill`. The report reads the verifier's
`reward.json`, runs `harbor analyze` with the task's `rubric.toml`, and fails
on a failed oracle, an errored trial, a reward below 1.0, a failed analysis, or
a leg that loaded no skill when `require_skills` is set.

A task the workflow runs keeps this contract:

- `environment/Dockerfile` pins lightcone-cli with `ARG LIGHTCONE_COMMIT=`;
- `tests/test.sh` writes `reward` to `/logs/verifier/reward.json`, with
  `agent_steps` and `skills_loaded` beside it when there is a trajectory;
- `rubric.toml`, if present, is what `harbor analyze` judges.

`eval-self.yml` runs the eval on this repository's own PRs that touch the
workflow or `snae-build`, against lightcone-cli and agent-skills main.
