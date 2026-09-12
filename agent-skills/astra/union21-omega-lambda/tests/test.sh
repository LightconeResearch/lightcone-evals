#!/bin/bash
set +e

# v3: one binary floor, two continuous science scores, two binary ASTRA
# flags. All five are measured and reported on every tier; only the REWARD
# formula is tier-dependent, because a prompt that never mentions ASTRA
# cannot be scored on ASTRA flags.
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
# PROMPT_VARIANT arrives from task.toml's [verifier.env], written by the same
# step that swapped in the instruction file — never inferred from the agent's
# artifacts, which would score the agent's behaviour to decide how to score
# the agent's behaviour.
#
# Harbor 0.22.0 parses /logs/verifier/reward.json as a flat map of
# name -> number and raises a pydantic ValidationError on any string or null
# value. So reward.json carries NUMBERS ONLY; everything non-numeric (which
# prompt ran, the raw fitted values) goes to the sibling details.json, which
# Harbor collects as an ordinary verifier log.

mkdir -p /logs/verifier

variant="${PROMPT_VARIANT:-baseline}"
case "$variant" in
  baseline|astra) ;;
  *) echo "unknown PROMPT_VARIANT '$variant'" >&2; exit 1 ;;
esac

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
  cat /logs/verifier/score.txt
  scores='{"omega_lambda": null, "omega_lambda_err": null, "omega_lambda_ref": 0.705, "omega_lambda_err_ref": 0.0415, "omega_lambda_score": 0.0, "omega_lambda_err_score": 0.0}'
fi
printf '%s\n' "$scores" | tee -a /logs/verifier/score.txt

# Collecting the agent's astra.yaml, best_fit.json, and hubble_diagram.png
# for human review is task.toml's top-level `artifacts` job (declarative
# source -> destination entries, landing under
# jobs/<ts>/<trial>/artifacts/), not this script's -- this file is scoring
# only. See task.toml for why and where.

SCORES="$scores" \
VARIANT="$variant" \
DELIVERABLES="$deliverables" \
SPEC_VALID="$spec_valid" \
EVIDENCE_VERIFIED="$evidence_verified" \
python3 - <<'PY'
import json, os

scores = json.loads(os.environ["SCORES"])
variant = os.environ["VARIANT"]
deliverables = int(os.environ["DELIVERABLES"])
spec_valid = int(os.environ["SPEC_VALID"])
evidence_verified = int(os.environ["EVIDENCE_VERIFIED"])

science = [deliverables, scores["omega_lambda_score"], scores["omega_lambda_err_score"]]
graded = science if variant == "baseline" else science + [spec_valid, evidence_verified]
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
            "prompt_variant": variant,
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
