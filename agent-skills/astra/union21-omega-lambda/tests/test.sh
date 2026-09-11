#!/bin/bash
set +e

mkdir -p /logs/verifier

points=0
spec_validity=0.0
analysis_executed=0.0
fit_correct=0.0
systematics_covariance=0.0
paper_reproduced=0.0
evidence_and_decision=0.0

python3 -m pytest /tests/test_spec_validity.py -rA -v \
  > /logs/verifier/spec-validity.txt 2>&1
rc=$?
cat /logs/verifier/spec-validity.txt
if [ "$rc" -eq 0 ]; then
  spec_validity=1.0
  points=$((points + 15))
fi

python3 -m pytest /tests/test_analysis_executed.py -rA -v \
  > /logs/verifier/analysis-executed.txt 2>&1
rc=$?
cat /logs/verifier/analysis-executed.txt
if [ "$rc" -eq 0 ]; then
  analysis_executed=1.0
  points=$((points + 15))
fi

python3 -m pytest /tests/test_fit_correct.py -rA -v \
  > /logs/verifier/fit-correct.txt 2>&1
rc=$?
cat /logs/verifier/fit-correct.txt
if [ "$rc" -eq 0 ]; then
  fit_correct=1.0
  points=$((points + 15))
fi

python3 -m pytest /tests/test_systematics_covariance.py -rA -v \
  > /logs/verifier/systematics-covariance.txt 2>&1
rc=$?
cat /logs/verifier/systematics-covariance.txt
if [ "$rc" -eq 0 ]; then
  systematics_covariance=1.0
  points=$((points + 20))
fi

python3 -m pytest /tests/test_paper_reproduced.py -rA -v \
  > /logs/verifier/paper-reproduced.txt 2>&1
rc=$?
cat /logs/verifier/paper-reproduced.txt
if [ "$rc" -eq 0 ]; then
  paper_reproduced=1.0
  points=$((points + 20))
fi

python3 -m pytest /tests/test_evidence_and_decision.py -rA -v \
  > /logs/verifier/evidence-and-decision.txt 2>&1
rc=$?
cat /logs/verifier/evidence-and-decision.txt
if [ "$rc" -eq 0 ]; then
  evidence_and_decision=1.0
  points=$((points + 15))
fi

cp /root/sn-cosmology/astra.yaml /logs/verifier/astra.yaml 2>/dev/null || true

printf -v reward '%d.%02d' "$((points / 100))" "$((points % 100))"
printf '%s\n' "$reward" > /logs/verifier/reward.txt
printf '{"reward": %s, "spec_validity": %s, "analysis_executed": %s, "fit_correct": %s, "systematics_covariance": %s, "paper_reproduced": %s, "evidence_and_decision": %s}\n' \
  "$reward" "$spec_validity" "$analysis_executed" "$fit_correct" "$systematics_covariance" "$paper_reproduced" "$evidence_and_decision" \
  > /logs/verifier/reward.json
exit 0
