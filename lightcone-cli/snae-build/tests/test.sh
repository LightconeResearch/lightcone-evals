#!/usr/bin/env bash
# The verifier observes the completed lifecycle; it never executes recipes.
set +e
LOGS="${LOGS_DIR:-/logs/verifier}"
mkdir -p "$LOGS"
export LOGS_DIR="$LOGS"
python3 "$(dirname "${BASH_SOURCE[0]}")/grade.py"
# If the grading process itself crashes, do not leave a missing/old reward.
if [ "$?" -ne 0 ]; then
  printf '0.0\n' > "$LOGS/reward.txt"
  printf '{"reward": 0.0, "verifier_error": 1.0}\n' > "$LOGS/reward.json"
fi
exit 0
