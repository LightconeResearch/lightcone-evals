# Task template

Harbor 1.4 split-layout task, matching what `lightcone-bench` runs. The layout
and task.toml fields are aligned with `harbor task init` (Harbor 0.22.0) — the
same files, same schema — enriched with the contracts this benchmark has
already learned the hard way. `harbor task init lightcone/<name> -p <stack>/`
is an equally valid starting point; this folder exists so those lessons come
along by default.

To start a new task, copy this folder into the folder for the stack under test
and rename it (the folder name should match `[task].name` minus the
`lightcone/` prefix):

```
cp -r template lightcone-cli/my-new-task
rm lightcone-cli/my-new-task/README.md
```

## Layout

| path | role |
|---|---|
| `task.toml` | metadata, timeouts, resources (schema 1.4) |
| `instruction.md` | the agent's prompt — never mentions scoring |
| `environment/Dockerfile` | the container; `COPY project /root/project` for task files |
| `environment/project/` | the working files the agent starts from (create it) |
| `solution/solve.sh` | scripted oracle solution — must drive the verifier to exactly 1.0 |
| `tests/test.sh` | verifier: writes `/logs/verifier/reward.{txt,json}`, always exits 0 |
| `tests/verifier.md` | rubric declaration (dimensions, weights) |

## Contracts (learned the hard way — don't break these)

- **Reward contract:** `/logs/verifier/reward.txt` and `reward.json` are the
  only outputs the harness reads. One JSON key per rubric dimension.
- **Oracle gate:** CI runs `solution/solve.sh` first and requires reward 1.0
  before any agent leg runs. A task whose oracle can't score 1.0 never ships.
- **Users:** the agent runs unprivileged with `HOME=/home/<user>`; the oracle
  and verifier run as root. Anything the agent needs must be world-readable
  (`a+rX`), and `/root` needs `chmod 711` for the workspace to be reachable.
- **Stack pin:** keep the literal `ARG LIGHTCONE_COMMIT=` line — CI's
  `materialize.sh` rewrites it to the `stack_ref` under test.
- **No baked-in skills:** skills are a run-time benchmark axis, never part of
  the image.
- Local smoke test: `harbor run -p <task-dir> -a oracle -e docker` from a
  checkout with Harbor 0.22.0 installed.

## Portability (what is Harbor-specific, what is not)

Tasks should survive a future switch of base layer (runner). The Harbor-specific
surface is deliberately thin:

- **`task.toml`** — the manifest format itself. All the *content* (timeouts,
  resources, network mode) is generic; only the schema is Harbor's.
- **Path contracts** — the verifier is copied to `/tests/` and must write
  `/logs/verifier/reward.{txt,json}`; the oracle's helpers live at `/solution/`.
  These literals appear only in `test.sh` and `solve.sh`.
- **`tests/verifier.md`** — rubric declaration carried over from SkillsBench;
  informational to Harbor but kept as the runner-neutral statement of scoring.

Everything else — `instruction.md`, `environment/Dockerfile` + project files,
the pytest test groups, the solution scripts — is plain files with no Harbor
dependency. A base-layer switch means writing a new manifest and re-pointing
the three path literals, not rewriting tasks.

Note: `harbor task init`'s stock `tests/test.sh` installs uv at verify time and
emits a CTRF report; ours instead bakes test deps into the image and writes a
per-dimension `reward.json`, which `lightcone-bench`'s `summarize.py` consumes.
Keep the per-dimension pattern.
