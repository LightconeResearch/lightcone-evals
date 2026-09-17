#!/bin/bash
set +e

mkdir -p /logs/verifier
git config --global --add safe.directory '*'
export PYTHONDONTWRITEBYTECODE=1

points=0
estimation=0.0
synchronous_execution=0.0
oversized_classification=0.0

python3 -m pytest -p no:cacheprovider /tests/test_estimation.py -rA -v \
  > /logs/verifier/estimation.txt 2>&1
rc=$?
cat /logs/verifier/estimation.txt
if [ "$rc" -eq 0 ]; then
  estimation=1.0
  points=$((points + 40))
fi

python3 -m pytest -p no:cacheprovider /tests/test_sync.py -rA -v \
  > /logs/verifier/synchronous-execution.txt 2>&1
rc=$?
cat /logs/verifier/synchronous-execution.txt
if [ "$rc" -eq 0 ]; then
  synchronous_execution=1.0
  points=$((points + 30))
fi

python3 -m pytest -p no:cacheprovider /tests/test_classification.py -rA -v \
  > /logs/verifier/oversized-classification.txt 2>&1
rc=$?
cat /logs/verifier/oversized-classification.txt
if [ "$rc" -eq 0 ]; then
  oversized_classification=1.0
  points=$((points + 30))
fi

cp /root/snae/astra.yaml /logs/verifier/astra.yaml 2>/dev/null || true
cp /root/snae/.lightcone/estimates.json /logs/verifier/estimates.json 2>/dev/null || true
cp /root/snae/results/baseline/.best_fit.manifest.json \
  /logs/verifier/best-fit-manifest.json 2>/dev/null || true
cp /root/snae/execution-plan.json /logs/verifier/execution-plan.json 2>/dev/null || true

git -C /root/snae log --all --oneline > /logs/verifier/git-history.txt 2>&1
printf -v reward '%d.%02d' "$((points / 100))" "$((points % 100))"
printf '%s\n' "$reward" > /logs/verifier/reward.txt
printf '{"reward": %s, "auditable_resource_estimation": %s, "local_synchronous_execution": %s, "unsupported_local_classification": %s}\n' \
  "$reward" "$estimation" "$synchronous_execution" "$oversized_classification" \
  > /logs/verifier/reward.json
exit 0
