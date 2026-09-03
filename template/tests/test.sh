#!/bin/bash
set +e

# Verifier entry point. Runs as root after the agent (or oracle) finishes.
# The reward contract: write /logs/verifier/reward.txt (a number in [0, 1])
# and /logs/verifier/reward.json ({"reward": ..., <one key per dimension>}).
# Always exit 0 — a scoring failure is a 0.0 reward, not a verifier crash.

mkdir -p /logs/verifier

points=0
dimension_one=0.0

# One pytest group per rubric dimension; capture output for the artifacts.
python3 -m pytest /tests/test_dimension_one.py -rA -v \
  > /logs/verifier/dimension-one.txt 2>&1
rc=$?
cat /logs/verifier/dimension-one.txt
if [ "$rc" -eq 0 ]; then
  dimension_one=1.0
  points=$((points + 100))
fi

# Copy key agent outputs into /logs/verifier/ so they land in the run
# artifacts even when scoring fails.
# cp /root/project/some-output.json /logs/verifier/ 2>/dev/null || true

printf -v reward '%d.%02d' "$((points / 100))" "$((points % 100))"
printf '%s\n' "$reward" > /logs/verifier/reward.txt
printf '{"reward": %s, "dimension_one": %s}\n' \
  "$reward" "$dimension_one" \
  > /logs/verifier/reward.json
exit 0
