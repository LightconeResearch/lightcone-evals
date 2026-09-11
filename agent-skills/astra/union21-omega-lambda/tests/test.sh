#!/bin/bash
set +e

mkdir -p /logs/verifier

points=0
spec_validity=0.0
analysis_executed=0.0
omega_lambda_value=0.0
omega_lambda_uncertainty=0.0
evidence_and_decision=0.0

python3 -m pytest /tests/test_spec_validity.py -rA -v \
  > /logs/verifier/spec-validity.txt 2>&1
rc=$?
cat /logs/verifier/spec-validity.txt
if [ "$rc" -eq 0 ]; then
  spec_validity=1.0
  points=$((points + 20))
fi

python3 -m pytest /tests/test_analysis_executed.py -rA -v \
  > /logs/verifier/analysis-executed.txt 2>&1
rc=$?
cat /logs/verifier/analysis-executed.txt
if [ "$rc" -eq 0 ]; then
  analysis_executed=1.0
  points=$((points + 20))
fi

python3 -m pytest /tests/test_omega_lambda_value.py -rA -v \
  > /logs/verifier/omega-lambda-value.txt 2>&1
rc=$?
cat /logs/verifier/omega-lambda-value.txt
if [ "$rc" -eq 0 ]; then
  omega_lambda_value=1.0
  points=$((points + 20))
fi

python3 -m pytest /tests/test_omega_lambda_uncertainty.py -rA -v \
  > /logs/verifier/omega-lambda-uncertainty.txt 2>&1
rc=$?
cat /logs/verifier/omega-lambda-uncertainty.txt
if [ "$rc" -eq 0 ]; then
  omega_lambda_uncertainty=1.0
  points=$((points + 20))
fi

python3 -m pytest /tests/test_evidence_and_decision.py -rA -v \
  > /logs/verifier/evidence-and-decision.txt 2>&1
rc=$?
cat /logs/verifier/evidence-and-decision.txt
if [ "$rc" -eq 0 ]; then
  evidence_and_decision=1.0
  points=$((points + 20))
fi

cp /root/sn-cosmology/astra.yaml /logs/verifier/astra.yaml 2>/dev/null || true

printf -v reward '%d.%02d' "$((points / 100))" "$((points % 100))"
printf '%s\n' "$reward" > /logs/verifier/reward.txt
printf '{"reward": %s, "spec_validity": %s, "analysis_executed": %s, "omega_lambda_value": %s, "omega_lambda_uncertainty": %s, "evidence_and_decision": %s}\n' \
  "$reward" "$spec_validity" "$analysis_executed" "$omega_lambda_value" "$omega_lambda_uncertainty" "$evidence_and_decision" \
  > /logs/verifier/reward.json
exit 0
