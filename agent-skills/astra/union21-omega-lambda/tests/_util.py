"""Shared, tolerant lookups for the union21-omega-lambda verifier.

The agent authors astra.yaml and chooses its own output layout, so these
tests search rather than hardcode paths or key names. Physics numbers and
validation outcomes are checked strictly; everything about *where* the agent
put things is not.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

import yaml

PROJECT = Path(os.environ.get("TASK_PROJECT_ROOT", "/root/sn-cosmology"))
SPEC_PATH = PROJECT / "astra.yaml"

SKIP_DIR_NAMES = {"data", ".git", ".lightcone", "__pycache__", ".venv"}

# Matches a key naming an Omega_Lambda-like quantity ("Omega_L", "omega_lambda",
# "OmegaLambda", ...) but not siblings like "Omega_m" or "Omega_L_sigma".
_OMEGA_KEY = re.compile(r"omega.*l(ambda)?$", re.I)
_SIGMA_KEY = re.compile(r"sigma|uncertainty|stderr|error", re.I)


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
    """Every plausible (Omega_Lambda, sigma_or_None, source_file) triple on disk."""
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


def iter_png_files():
    for path in PROJECT.rglob("*.png"):
        if not _in_skipped_dir(path):
            yield path
