"""Shared lookups for the union21-omega-lambda verifier.

The prompt (both instruction.md and instruction-astra.md) names an exact
output contract: `/root/sn-cosmology/results/best_fit.json` with keys
`omega_lambda` and `omega_lambda_err`, and
`/root/sn-cosmology/results/hubble_diagram.png`. The science_level rungs
read that named contract strictly — no globbing, no key-name pattern
matching — because the prompt asked for it plainly and "the answer exists
somewhere else" is a real failure mode worth scoring as level 0, not
compensating for.

The looser glob+pattern search this module used to score with is kept below
as `find_omega_lambda_estimates()`, but only for the `answer_found_elsewhere`
diagnostic (see check_answer_elsewhere.py) — it never affects reward.

ASTRA spec authoring (astra.yaml's own paths, decision IDs, option IDs) is a
different matter: the agent chooses those, so `test_astra_spec_valid.py` and
`test_astra_evidence_and_decisions.py` stay tolerant on IDs and pattern-match
option text, exactly as before.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import yaml

PROJECT = Path(os.environ.get("TASK_PROJECT_ROOT", "/root/sn-cosmology"))
SPEC_PATH = PROJECT / "astra.yaml"

NAMED_BEST_FIT_PATH = PROJECT / "results" / "best_fit.json"
NAMED_FIGURE_PATH = PROJECT / "results" / "hubble_diagram.png"

SKIP_DIR_NAMES = {"data", ".git", ".lightcone", "__pycache__", ".venv"}

# Matches a key naming an Omega_Lambda-like quantity ("Omega_L", "omega_lambda",
# "OmegaLambda", ...) but not siblings like "Omega_m" or "Omega_L_sigma".
_OMEGA_KEY = re.compile(r"omega.*l(ambda)?$", re.I)
_SIGMA_KEY = re.compile(r"sigma|uncertainty|stderr|error", re.I)


def read_named_best_fit() -> dict | None:
    """Strictly read the prompt-specified best_fit.json; None if missing or unparseable."""
    if not NAMED_BEST_FIT_PATH.is_file():
        return None
    try:
        data = json.loads(NAMED_BEST_FIT_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def _in_skipped_dir(path: Path) -> bool:
    return any(part in SKIP_DIR_NAMES for part in path.relative_to(PROJECT).parts)


def _iter_record_files():
    for path in PROJECT.rglob("*"):
        if not path.is_file() or path == SPEC_PATH or _in_skipped_dir(path):
            continue
        if path.suffix.lower() in {".json", ".yaml", ".yml"}:
            yield path


def _load(path: Path):
    try:
        text = path.read_text(encoding="utf-8")
        return json.loads(text) if path.suffix.lower() == ".json" else yaml.safe_load(text)
    except Exception:
        return None


def _walk_dicts(obj):
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from _walk_dicts(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from _walk_dicts(item)


def find_omega_lambda_estimates() -> list[tuple[float, float | None, Path]]:
    """Every plausible (Omega_Lambda, sigma_or_None, source_file) triple on disk.

    Diagnostic only (see module docstring) — not used by any scored dimension.
    """
    results = []
    for path in _iter_record_files():
        data = _load(path)
        if data is None:
            continue
        for node in _walk_dicts(data):
            omega_value = None
            sigma_value = None
            for key, value in node.items():
                if not isinstance(value, (int, float)) or isinstance(value, bool):
                    continue
                if _OMEGA_KEY.search(str(key)):
                    omega_value = float(value)
                elif _SIGMA_KEY.search(str(key)):
                    sigma_value = float(value)
            if omega_value is not None:
                results.append((omega_value, sigma_value, path))
    return results
