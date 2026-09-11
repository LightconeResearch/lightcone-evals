"""Shared lookups for the union21-omega-lambda verifier.

Two files are the single source of truth here, not this module's own code:

- `contract.json`, baked into the project at `environment/project/contract.json`
  (so it lands at `$PROJECT/contract.json` for the agent, solve.sh, AND these
  tests alike, all of which already agree on `$PROJECT`/`TASK_PROJECT_ROOT`)
  — the output contract both instruction files state in prose: the project
  root, the named result paths, and the two JSON key names. It is safe for
  the agent to see, since the prompt already discloses all of it verbatim.
- `tolerances.json`, next to this file in `tests/` (never baked into the
  project — these are the science-dimension pass/fail windows, and exposing
  them to the agent would leak the scoring thresholds the ablation is
  measuring against).

The science dimensions read the named contract strictly — no globbing, no
key-name pattern matching — because the prompt states the contract in plain
prose, so "the answer exists somewhere in the agent's head or in stdout" is
a real failure worth catching as a failed science dimension, not one the
verifier should compensate for by searching harder.

ASTRA spec authoring (astra.yaml's own paths, decision IDs, option IDs) is a
different matter: the agent chooses those, so `test_astra.py` stays tolerant there.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

PROJECT = Path(os.environ.get("TASK_PROJECT_ROOT", "/root/sn-cosmology"))
SPEC_PATH = PROJECT / "astra.yaml"

# PROJECT has to be a literal default here: it is where contract.json itself
# lives, so it can't be derived from the contract file it locates.
_CONTRACT = json.loads((PROJECT / "contract.json").read_text(encoding="utf-8"))
_TOLERANCES = json.loads((Path(__file__).parent / "tolerances.json").read_text(encoding="utf-8"))

NAMED_BEST_FIT_PATH = PROJECT / _CONTRACT["best_fit_path"]
NAMED_FIGURE_PATH = PROJECT / _CONTRACT["figure_path"]
OMEGA_LAMBDA_KEY = _CONTRACT["omega_lambda_key"]
OMEGA_LAMBDA_ERR_KEY = _CONTRACT["omega_lambda_err_key"]

FIT_AND_FIGURE_OMEGA_LAMBDA = tuple(_TOLERANCES["fit_and_figure_omega_lambda"])
SYSTEMATICS_OMEGA_LAMBDA_ERR = tuple(_TOLERANCES["systematics_covariance_omega_lambda_err"])
PAPER_OMEGA_LAMBDA = tuple(_TOLERANCES["paper_reproduced_omega_lambda"])
PAPER_OMEGA_LAMBDA_ERR = tuple(_TOLERANCES["paper_reproduced_omega_lambda_err"])


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
