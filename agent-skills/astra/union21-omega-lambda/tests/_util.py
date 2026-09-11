"""Shared lookups for the union21-omega-lambda verifier.

Two files are the single source of truth here, not this module's own code:

- `contract.json`, baked into the project at `environment/project/contract.json`
  (so it lands at `$PROJECT/contract.json` for the agent, solve.sh, AND these
  tests alike, all of which already agree on `$PROJECT`/`TASK_PROJECT_ROOT`)
  — the output contract both instruction files state in prose: the project
  root, the named result paths, and the two JSON key names. It is safe for
  the agent to see, since the prompt already discloses all of it verbatim.
- `tolerances.json`, next to this file in `tests/` (never baked into the
  project — these are the science_level pass/fail windows, and exposing
  them to the agent would leak the scoring thresholds the ablation is
  measuring against).

The `science_level` rungs read the named contract strictly — no globbing, no
key-name pattern matching — because the prompt states the contract in plain
prose, so "the answer exists somewhere in the agent's head or in stdout" is
a real failure worth catching as science_level 0, not one the verifier
should compensate for by searching harder.

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

# PROJECT has to be a literal default here too: it is where contract.json
# itself lives, so it can't be derived from the contract file it locates.
# It must agree with the Dockerfile's COPY/WORKDIR destination and
# solve.sh's PROJECT; the check below catches drift between them.
_CONTRACT = json.loads((PROJECT / "contract.json").read_text(encoding="utf-8"))
if _CONTRACT["project_root"] != str(PROJECT):
    raise RuntimeError(
        f"contract.json's project_root ({_CONTRACT['project_root']!r}) disagrees "
        f"with PROJECT ({str(PROJECT)!r})"
    )
_TOLERANCES = json.loads((Path(__file__).parent / "tolerances.json").read_text(encoding="utf-8"))

NAMED_BEST_FIT_PATH = PROJECT / _CONTRACT["best_fit_path"]
NAMED_FIGURE_PATH = PROJECT / _CONTRACT["figure_path"]
OMEGA_LAMBDA_KEY = _CONTRACT["omega_lambda_key"]
OMEGA_LAMBDA_ERR_KEY = _CONTRACT["omega_lambda_err_key"]

LEVEL_1_OMEGA_LAMBDA = tuple(_TOLERANCES["level_1_omega_lambda"])
LEVEL_2_OMEGA_LAMBDA_ERR = tuple(_TOLERANCES["level_2_omega_lambda_err"])
LEVEL_3_OMEGA_LAMBDA = tuple(_TOLERANCES["level_3_omega_lambda"])
LEVEL_3_OMEGA_LAMBDA_ERR = tuple(_TOLERANCES["level_3_omega_lambda_err"])

SKIP_DIR_NAMES = {"data", ".git", ".lightcone", "__pycache__", ".venv"}

# Matches a key naming an Omega_Lambda-like quantity ("Omega_L", "omega_lambda",
# "OmegaLambda", ...) but not siblings like "Omega_m" or "Omega_L_sigma". Used
# only by the answer_found_elsewhere diagnostic, never by a scored dimension.
_OMEGA_KEY = re.compile(r"omega.*l(ambda)?$", re.I)
_SIGMA_KEY = re.compile(r"sigma|uncertainty|stderr|error", re.I)


def is_numeric(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


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
                if not is_numeric(value):
                    continue
                if _OMEGA_KEY.search(str(key)):
                    omega_value = float(value)
                elif _SIGMA_KEY.search(str(key)):
                    sigma_value = float(value)
            if omega_value is not None:
                results.append((omega_value, sigma_value, path))
    return results
