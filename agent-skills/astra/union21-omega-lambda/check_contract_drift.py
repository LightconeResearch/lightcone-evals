#!/usr/bin/env python3
"""Task-consistency check: do both tasks' instruction.md and both tasks'
task.toml artifact lists agree with contract.json, the single source of
truth for the output contract?

The two tasks are this directory (the baseline prompt) and the sibling
union21-omega-lambda-astra (the ASTRA prompt), which symlinks environment/,
tests/ and solution/ back here and differs only in instruction.md and
task.toml.

This is NOT part of the scored verifier and is deliberately not wired into
tests/test.sh, because it cannot run there: Harbor only copies tests/ ->
/tests and solution/ -> /solution into the environment container
(see harbor/models/trial/paths.py and harbor/agents/oracle.py in the
installed `harbor` package) -- instruction.md and task.toml live at each
task's root and are read by Harbor on the *host* to
build the agent's prompt and the trial's configuration. None of them ever
land in any container, in either the oracle or the verifier phase, so a
check that reads them has to run against a plain checkout instead. An agent
must never be penalized for these files drifting, which is the other reason
this stays outside test.sh: a failure here is a task-authoring bug, not a
property of the agent's run.

task.toml is checked as plain text (substring search for the exact
artifact-source strings), not parsed as TOML, so this script has no
dependency beyond the standard library that predates Python 3.11's
`tomllib` -- the system `python3` here is 3.9.

Run this after editing contract.json, either task's instruction.md, or
either task.toml's artifacts list:
    python3 check_contract_drift.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

TASK_ROOT = Path(__file__).resolve().parent
CONTRACT = json.loads((TASK_ROOT / "environment" / "project" / "contract.json").read_text())

# Every task dir sharing this contract: this one and its ASTRA-prompt sibling.
TASK_DIRS = (TASK_ROOT, TASK_ROOT.parent / "union21-omega-lambda-astra")

REQUIRED_VALUES = (
    f"{CONTRACT['project_root']}/{CONTRACT['best_fit_path']}",
    f"{CONTRACT['project_root']}/{CONTRACT['figure_path']}",
    CONTRACT["omega_lambda_key"],
    CONTRACT["omega_lambda_err_key"],
)

TASK_TOML_REQUIRED_SOURCES = (
    f"{CONTRACT['project_root']}/astra.yaml",
    f"{CONTRACT['project_root']}/{CONTRACT['best_fit_path']}",
    f"{CONTRACT['project_root']}/{CONTRACT['figure_path']}",
)


def check_instruction(task_dir: Path, problems: list[str]) -> None:
    path = task_dir / "instruction.md"
    label = f"{task_dir.name}/instruction.md"
    if not path.is_file():
        problems.append(f"{label}: file does not exist")
        return
    text = path.read_text(encoding="utf-8")
    for value in REQUIRED_VALUES:
        if value not in text:
            problems.append(f"{label}: missing required contract value {value!r}")


def check_task_toml(task_dir: Path, problems: list[str]) -> None:
    path = task_dir / "task.toml"
    label = f"{task_dir.name}/task.toml"
    if not path.is_file():
        problems.append(f"{label}: file does not exist")
        return
    text = path.read_text(encoding="utf-8")
    for source in TASK_TOML_REQUIRED_SOURCES:
        if f'"{source}"' not in text:
            problems.append(f"{label}: no artifact entry with source {source!r}")


def main() -> int:
    problems: list[str] = []
    for task_dir in TASK_DIRS:
        check_instruction(task_dir, problems)
        check_task_toml(task_dir, problems)

    if problems:
        print("CONTRACT DRIFT:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    names = ", ".join(d.name for d in TASK_DIRS)
    print(f"OK: instruction.md and task.toml agree with contract.json in: {names}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
