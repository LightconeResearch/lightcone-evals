#!/usr/bin/env python3
"""Diagnostic only — never scored, never affects reward or science_level.

Distinguishes "the agent couldn't do the physics" from "the agent did the
physics and filed it somewhere other than the named results/best_fit.json"
by re-running the old glob+pattern search for a plausible Omega_Lambda value
anywhere else under the project. Prints 0 or 1 to stdout (test.sh captures it
as the answer_found_elsewhere key) and writes the locations found, if any,
to /logs/verifier/answer-elsewhere.txt (not reward.json: summarize.py only
keeps numeric keys, and a path is not one).
"""

from __future__ import annotations

from pathlib import Path

from _util import NAMED_BEST_FIT_PATH, find_omega_lambda_estimates

REPORT_PATH = Path("/logs/verifier/answer-elsewhere.txt")


def main() -> int:
    elsewhere = [
        (omega, sigma, path)
        for omega, sigma, path in find_omega_lambda_estimates()
        if path != NAMED_BEST_FIT_PATH
    ]

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    if elsewhere:
        lines = [f"{omega} (sigma={sigma}) in {path}" for omega, sigma, path in elsewhere]
        REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(1)
    else:
        REPORT_PATH.write_text("none\n", encoding="utf-8")
        print(0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
