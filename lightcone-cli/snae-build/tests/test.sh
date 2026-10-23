#!/bin/bash
# Verifier (runs as root after the agent). Three deterministic dimensions,
# mirroring lightcone-cli's own eval gate (astra validate, lc materialize
# --check, ro-crate-metadata.json) with partial credit for outputs built:
#   spec_valid        0.25  astra validate astra.yaml passes
#   outputs_current   0.50  fraction of declared outputs `current` in lc status --json
#   publication_ready 0.25  lc materialize --check is up to date with >=1 current
#                           output, and ro-crate-metadata.json exists
# Two facts about how the agent got there ride along unweighted, read from
# the ATIF trajectory Harbor syncs to /logs/agent before verification, and
# only when there is one (the oracle has none):
#   agent_steps             trajectory steps the agent took
#   skills_loaded           1 if the agent loaded a skill, else 0
# Always exits 0; scoring problems are a 0.0, not a crash.
set +e

PROJECT="${PROJECT:-/root/snae-build}"
LOGS="${LOGS_DIR:-/logs/verifier}"
mkdir -p "$LOGS"

# The repository is owned by the agent user; git refuses to read another
# user's repo without this.
git config --global --add safe.directory '*' 2>/dev/null

spec_valid=0.0
outputs_current=0.0
publication_ready=0.0

if cd "$PROJECT"; then
  if astra validate astra.yaml > "$LOGS/astra-validate.txt" 2>&1; then
    spec_valid=1.0
  fi
  cat "$LOGS/astra-validate.txt"

  lc status > "$LOGS/lc-status.txt" 2>&1
  cat "$LOGS/lc-status.txt"
  lc status --json > "$LOGS/lc-status.json" 2> "$LOGS/lc-status.err"
  outputs_current=$(python3 - "$LOGS/lc-status.json" <<'PY'
import json, sys
try:
    outputs = json.load(open(sys.argv[1])).get("outputs") or []
except Exception:
    outputs = []
current = sum(1 for o in outputs if o.get("status") == "current")
print(f"{current / len(outputs):.4f}" if outputs else "0.0")
PY
)

  lc materialize --check --json > "$LOGS/lc-check.json" 2> "$LOGS/lc-check.err"
  if python3 - "$LOGS/lc-check.json" <<'PY'
import json, sys
try:
    report = json.load(open(sys.argv[1]))
except Exception:
    sys.exit(1)
sys.exit(0 if report.get("up_to_date") and len(report.get("current") or []) > 0 else 1)
PY
  then
    if [ -f ro-crate-metadata.json ]; then
      publication_ready=1.0
    fi
  fi

  # Keep what explains the score in the artifacts.
  cp astra.yaml "$LOGS/astra.yaml" 2>/dev/null || true
  cp pyproject.toml "$LOGS/pyproject.toml" 2>/dev/null || true
  cp ro-crate-metadata.json "$LOGS/ro-crate-metadata.json" 2>/dev/null || true
  git log --oneline > "$LOGS/git-log.txt" 2>&1 || true
  ls -laR results > "$LOGS/results-listing.txt" 2>&1 || true
  ls -la scripts src > "$LOGS/scripts-listing.txt" 2>&1 || true
fi

read -r reward < <(python3 -c "print(f'{0.25*$spec_valid + 0.5*$outputs_current + 0.25*$publication_ready:.4f}')")
printf '%s\n' "$reward" > "$LOGS/reward.txt"
python3 - "$LOGS/reward.json" "${AGENT_LOGS_DIR:-/logs/agent}/trajectory.json" \
  "$reward" "$spec_valid" "$outputs_current" "$publication_ready" <<'PY'
import json, sys
out, trajectory, *scores = sys.argv[1:]
result = dict(zip(["reward", "spec_valid", "outputs_current", "publication_ready"],
                  map(float, scores)))
try:
    steps = json.load(open(trajectory)).get("steps") or []
except Exception:
    steps = None
if steps is not None:
    calls = [c for s in steps for c in s.get("tool_calls") or []]
    result["agent_steps"] = sum(1 for s in steps if s.get("source") == "agent")
    # A harness's Skill tool, or reading a SKILL.md by hand (codex has no tool)
    result["skills_loaded"] = int(any(
        (c.get("function_name") or "").lower() == "skill"
        or "SKILL.md" in json.dumps(c.get("arguments"))
        for c in calls))
open(out, "w").write(json.dumps(result) + "\n")
PY
cat "$LOGS/reward.json"
exit 0
