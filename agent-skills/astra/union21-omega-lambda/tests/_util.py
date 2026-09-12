"""Shared lookups for the union21-omega-lambda verifier.

Two files are the single source of truth here, not this module's own code:

- `contract.json`, baked into the project at `environment/project/contract.json`
  (so it lands at `$PROJECT/contract.json` for the agent, solve.sh, AND these
  tests alike, all of which already agree on `$PROJECT`/`TASK_PROJECT_ROOT`)
  — the output contract both instruction files state in prose: the project
  root, the named result paths, and the two JSON key names. It is safe for
  the agent to see, since the prompt already discloses all of it verbatim.
- `reference.json`, next to this file in `tests/` (never baked into the
  project — these are the published values the continuous science scores are
  measured against, and exposing them to the agent would hand over the
  answer the task exists to make it derive).

The science scores read the named contract strictly — no globbing, no
key-name pattern matching — because the prompt states the contract in plain
prose, so "the answer exists somewhere in the agent's head or in stdout" is
a real failure worth catching, not one the verifier should compensate for by
searching harder.

ASTRA spec authoring (astra.yaml's own paths, decision IDs, option IDs) is a
different matter: the agent chooses those, so `test_astra.py` stays tolerant there.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path

PROJECT = Path(os.environ.get("TASK_PROJECT_ROOT", "/root/sn-cosmology"))
SPEC_PATH = PROJECT / "astra.yaml"

# PROJECT has to be a literal default here: it is where contract.json itself
# lives, so it can't be derived from the contract file it locates.
_CONTRACT = json.loads((PROJECT / "contract.json").read_text(encoding="utf-8"))
_REFERENCE = json.loads((Path(__file__).parent / "reference.json").read_text(encoding="utf-8"))

NAMED_BEST_FIT_PATH = PROJECT / _CONTRACT["best_fit_path"]
NAMED_FIGURE_PATH = PROJECT / _CONTRACT["figure_path"]
OMEGA_LAMBDA_KEY = _CONTRACT["omega_lambda_key"]
OMEGA_LAMBDA_ERR_KEY = _CONTRACT["omega_lambda_err_key"]

# Suzuki et al. 2012, SN-only, flat LCDM: Omega_Lambda = 0.705 (+0.040, -0.043),
# symmetrised to a single sigma of 0.0415. The log-width is the factor by which
# a reported sigma may miss the paper's before the error score falls to exp(-1/2).
OMEGA_LAMBDA_REF = _REFERENCE["omega_lambda_ref"]
OMEGA_LAMBDA_ERR_REF = _REFERENCE["omega_lambda_err_ref"]
OMEGA_LAMBDA_ERR_LOG_WIDTH = _REFERENCE["omega_lambda_err_log_width"]


def is_numeric(value: object) -> bool:
    """True for a real, finite number.

    Non-finite values are excluded deliberately. Python's `json.loads` accepts
    the bare tokens `NaN`, `Infinity` and `-Infinity`, which RFC 8259 does not,
    and `json.dump` writes them straight back out — so a diverged fit writing
    `{"omega_lambda": NaN}` would otherwise produce a `reward.json` that no
    conforming JSON parser can read, and a NaN reward that silently poisons the
    mean over a whole sweep. A NaN is not an answer; it scores 0 like any other
    unusable value.
    """
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    return math.isfinite(value)


def read_named_best_fit() -> dict | None:
    """Strictly read the prompt-specified best_fit.json; None if missing or unparseable."""
    if not NAMED_BEST_FIT_PATH.is_file():
        return None
    try:
        data = json.loads(NAMED_BEST_FIT_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def named_value(key: str) -> float | None:
    """The numeric value stored under `key` in the named best_fit.json, or None."""
    record = read_named_best_fit()
    if record is None:
        return None
    value = record.get(key)
    return float(value) if is_numeric(value) else None
