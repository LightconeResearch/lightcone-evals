#!/usr/bin/env python3
"""Task-consistency check: do instruction.md and instruction-astra.md agree
with contract.json, the single source of truth for the output contract?

This is NOT part of the scored verifier and is deliberately not wired into
tests/test.sh, because it cannot run there: Harbor only copies tests/ ->
/tests and solution/ -> /solution into the environment container
(see harbor/models/trial/paths.py and harbor/agents/oracle.py in the
installed `harbor` package) -- instruction.md and instruction-astra.md live
at the task root and are read by Harbor on the *host* to build the agent's
prompt. They never land in any container, in either the oracle or the
verifier phase, so a check that reads their prose has to run against a
plain checkout instead. An agent must never be penalized for these files
drifting, which is the other reason this stays outside test.sh: a failure
here is a task-authoring bug, not a property of the agent's run.

Run this after editing contract.json or either instruction file:
    python3 check_contract_drift.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

TASK_ROOT = Path(__file__).resolve().parent
CONTRACT = json.loads((TASK_ROOT / "environment" / "project" / "contract.json").read_text())

INSTRUCTION_FILES = ("instruction.md", "instruction-astra.md")

REQUIRED_VALUES = (
    f"{CONTRACT['project_root']}/{CONTRACT['best_fit_path']}",
    f"{CONTRACT['project_root']}/{CONTRACT['figure_path']}",
    CONTRACT["omega_lambda_key"],
    CONTRACT["omega_lambda_err_key"],
)

# The sentence both instruction files must state identically. Anchored on
# its opening words through the figure path's filename plus a period, since
# that is always the last thing the sentence names.
SENTENCE_START = "Save the constraint to "
SENTENCE_END = f"{Path(CONTRACT['figure_path']).name}`."


def extract_contract_sentence(text: str) -> str | None:
    start = text.find(SENTENCE_START)
    if start == -1:
        return None
    end = text.find(SENTENCE_END, start)
    if end == -1:
        return None
    return text[start : end + len(SENTENCE_END)]


def main() -> int:
    problems: list[str] = []
    sentences: dict[str, str] = {}

    for name in INSTRUCTION_FILES:
        path = TASK_ROOT / name
        if not path.is_file():
            problems.append(f"{name}: file does not exist")
            continue
        text = path.read_text(encoding="utf-8")

        for value in REQUIRED_VALUES:
            if value not in text:
                problems.append(f"{name}: missing required contract value {value!r}")

        sentence = extract_contract_sentence(text)
        if sentence is None:
            problems.append(f"{name}: could not find the output-contract sentence")
        else:
            sentences[name] = sentence

    if len(sentences) == len(INSTRUCTION_FILES) and len(set(sentences.values())) > 1:
        problems.append(
            "instruction files disagree on the output-contract sentence:\n"
            + "\n".join(f"  {name}: {sentence!r}" for name, sentence in sentences.items())
        )

    if problems:
        print("CONTRACT DRIFT:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        return 1

    print("OK: instruction.md and instruction-astra.md agree with contract.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
