#!/bin/bash
set +e
# One 0/1 dimension per answer.json key; reward = all-or-nothing min of them.
# Expected values are re-derived here from the pristine spec in /tests/spec with
# astra's resolver and `astra universe check` (derive_expected.py) and must equal
# /tests/expected.json; a mismatch means astra's semantics drifted under the
# task, and scores 0 with a DRIFT line in expected_drift.txt.
# The checks import astra from its tool environment (the image installs it
# with `uv tool install`, so the system python3 does not have it).
ASTRA_PY=/opt/uv-tools/astra-tools/bin/python
mkdir -p /logs/verifier
"$ASTRA_PY" /tests/derive_expected.py /tests/spec > /logs/verifier/derived.json 2> /logs/verifier/expected_drift.txt
"$ASTRA_PY" /tests/check_answers.py
exit 0
