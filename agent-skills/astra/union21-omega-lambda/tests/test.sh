#!/bin/bash
set +e

# One binary floor, two continuous science scores, two binary ASTRA flags.
# All five are measured, reported, and graded identically for every task:
#
#   reward = mean(deliverables, omega_lambda_score, omega_lambda_err_score,
#                 spec_valid, evidence_verified)
#
# The baseline task's prompt never asks for ASTRA, so its spec_valid and
# evidence_verified are measured 0 and its reward is capped at 0.60 by
# construction. Compare rewards within a task, not across tasks.
#
#   deliverables            0/1  the named best_fit.json has both numeric
#                                values AND the named PNG exists and decodes
#   omega_lambda_score      0-1  exp(-0.5 * ((omega - 0.705) / 0.0415)^2)
#   omega_lambda_err_score  0-1  exp(-0.5 * (ln(sigma / 0.0415) / ln(1.4))^2)
#   spec_valid              0/1  astra validate + the prompt's three nouns
#   evidence_verified       0/1  astra paper verify-quote on a Suzuki citation
#
# The two continuous scores cannot be pytest verdicts (pytest is pass/fail),
# so they come from /tests/score.py, which prints them as JSON.
#

# Harbor 0.22.0 parses /logs/verifier/reward.json as a flat map of
# name -> number and raises a pydantic ValidationError on any string or null
# value. So reward.json carries NUMBERS ONLY; the raw fitted values, which
# are null when the agent produced nothing readable, go to the sibling
# details.json, which Harbor collects as an ordinary verifier log.

mkdir -p /logs/verifier

# Runs one binary dimension's pytest selection, echoes its log to the
# verifier's stdout, and assigns 1/0 to the shell variable named after it.
run_dimension() { # $1 name  $2 test module
  python3 -m pytest "$2" -k "$1" -rA -v > "/logs/verifier/$1.txt" 2>&1
  local rc=$?
  cat "/logs/verifier/$1.txt"
  if [ "$rc" -eq 0 ]; then eval "$1=1"; else eval "$1=0"; fi
}

run_dimension deliverables /tests/test_science.py
run_dimension spec_valid /tests/test_astra.py
run_dimension evidence_verified /tests/test_astra.py

scores=$(python3 /tests/score.py 2>/logs/verifier/score.txt)
if [ -z "$scores" ]; then
  # score.py itself broke. Fall back to an all-zero fragment, still reading the
  # reference values from tests/reference.json rather than restating them here,
  # so the one place they live stays the one place they live.
  cat /logs/verifier/score.txt
  scores=$(python3 -c 'import json; r = json.load(open("/tests/reference.json")); print(json.dumps({"omega_lambda": None, "omega_lambda_err": None, "omega_lambda_ref": r["omega_lambda_ref"], "omega_lambda_err_ref": r["omega_lambda_err_ref"], "omega_lambda_score": 0.0, "omega_lambda_err_score": 0.0}))')
fi
printf '%s\n' "$scores" | tee -a /logs/verifier/score.txt

# Collecting the agent's astra.yaml, best_fit.json, and hubble_diagram.png
# for human review is task.toml's top-level `artifacts` job (declarative
# source -> destination entries, landing under
# jobs/<ts>/<trial>/artifacts/), not this script's -- this file is scoring
# only. See task.toml for why and where.

SCORES="$scores" \
DELIVERABLES="$deliverables" \
SPEC_VALID="$spec_valid" \
EVIDENCE_VERIFIED="$evidence_verified" \
python3 - <<'PY'
import json, os

scores = json.loads(os.environ["SCORES"])
deliverables = int(os.environ["DELIVERABLES"])
spec_valid = int(os.environ["SPEC_VALID"])
evidence_verified = int(os.environ["EVIDENCE_VERIFIED"])

graded = [
    deliverables,
    scores["omega_lambda_score"],
    scores["omega_lambda_err_score"],
    spec_valid,
    evidence_verified,
]
reward = round(sum(graded) / len(graded), 2)

with open("/logs/verifier/reward.json", "w") as handle:
    json.dump(
        {
            "reward": reward,
            "deliverables": deliverables,
            "omega_lambda_score": scores["omega_lambda_score"],
            "omega_lambda_err_score": scores["omega_lambda_err_score"],
            "spec_valid": spec_valid,
            "evidence_verified": evidence_verified,
        },
        handle,
    )
    handle.write("\n")

with open("/logs/verifier/details.json", "w") as handle:
    json.dump(
        {
            "omega_lambda": scores["omega_lambda"],
            "omega_lambda_err": scores["omega_lambda_err"],
            "omega_lambda_ref": scores["omega_lambda_ref"],
            "omega_lambda_err_ref": scores["omega_lambda_err_ref"],
        },
        handle,
    )
    handle.write("\n")

with open("/logs/verifier/reward.txt", "w") as handle:
    handle.write(f"{reward:.2f}\n")
PY

cat /logs/verifier/reward.json
cat /logs/verifier/details.json
exit 0
