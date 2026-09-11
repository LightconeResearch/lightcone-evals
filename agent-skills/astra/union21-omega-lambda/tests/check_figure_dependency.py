#!/usr/bin/env python3
"""Diagnostic only — never scored, never affects reward or astra_spec_valid.

Neither instruction file asks for a particular dependency structure between
the figure and metric outputs, and `astra validate` happily accepts a figure
whose recipe computes the fit inline from the raw data. So
astra_spec_valid does not require it (see test_astra_spec_valid.py). But
whether the figure declares the metric output as an upstream dependency is
exactly the kind of provenance structure ASTRA exists to represent, so it's
worth knowing about without penalizing its absence. Prints 0 or 1 to stdout
(test.sh captures it as the figure_depends_on_output key).
"""

from __future__ import annotations

import yaml

from _util import SPEC_PATH


def main() -> int:
    if not SPEC_PATH.is_file():
        print(0)
        return 0
    try:
        spec = yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))
    except Exception:
        print(0)
        return 0
    outputs = (spec or {}).get("outputs") or []
    output_ids = {output["id"] for output in outputs if "id" in output}
    figures = [output for output in outputs if output.get("type") == "figure"]

    def depends_on_another_output(figure: dict) -> bool:
        upstream = set(figure.get("inputs") or [])
        return bool(upstream & (output_ids - {figure.get("id")}))

    print(1 if any(depends_on_another_output(f) for f in figures) else 0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
