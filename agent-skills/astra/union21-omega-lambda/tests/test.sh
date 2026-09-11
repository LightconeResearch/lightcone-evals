#!/bin/bash
set +e

# Five independent 0/1 dimensions, all measured and all reported on every
# tier. Three science dimensions (licensed by both instruction files) and
# two ASTRA dimensions (licensed only by instruction-astra.md). There is no
# ladder: each dimension runs unconditionally and scores on its own terms.
#
# Only the REWARD is tier-dependent. A prompt that never mentions ASTRA
# cannot be scored on ASTRA flags, so the baseline reward is the mean of the
# three science dimensions and the astra-prompt reward is the mean of all
# five. PROMPT_VARIANT arrives from task.toml's [verifier.env], written by
# the same step that swapped in the instruction file — never inferred from
# the agent's artifacts, which would score the agent's behaviour to decide
# how to score the agent's behaviour.

mkdir -p /logs/verifier

variant="${PROMPT_VARIANT:-baseline}"

# Runs one dimension's pytest selection, echoes its log to the verifier's
# stdout, and assigns 1/0 to the shell variable named after the dimension.
run_dimension() { # $1 name  $2 test module
  python3 -m pytest "$2" -k "$1" -rA -v > "/logs/verifier/$1.txt" 2>&1
  local rc=$?
  cat "/logs/verifier/$1.txt"
  if [ "$rc" -eq 0 ]; then eval "$1=1"; else eval "$1=0"; fi
}

run_dimension fit_and_figure /tests/test_science.py
run_dimension systematics_covariance /tests/test_science.py
run_dimension paper_reproduced /tests/test_science.py
run_dimension spec_valid /tests/test_astra.py
run_dimension evidence_verified /tests/test_astra.py

# Collecting the agent's astra.yaml, best_fit.json, and hubble_diagram.png
# for human review is task.toml's top-level `artifacts` job (declarative
# source -> destination entries, landing under
# jobs/<ts>/<trial>/artifacts/), not this script's -- this file is scoring
# only. See task.toml for why and where.

case "$variant" in
  baseline) reward=$(python3 -c "print(f'{(${fit_and_figure} + ${systematics_covariance} + ${paper_reproduced}) / 3:.2f}')") ;;
  astra)    reward=$(python3 -c "print(f'{(${fit_and_figure} + ${systematics_covariance} + ${paper_reproduced} + ${spec_valid} + ${evidence_verified}) / 5:.2f}')") ;;
  *) echo "unknown PROMPT_VARIANT '$variant'" >&2; exit 1 ;;
esac

printf '%s\n' "$reward" > /logs/verifier/reward.txt
printf '{"reward": %s, "prompt_variant": "%s", "fit_and_figure": %d, "systematics_covariance": %d, "paper_reproduced": %d, "spec_valid": %d, "evidence_verified": %d}\n' \
  "$reward" "$variant" "$fit_and_figure" "$systematics_covariance" "$paper_reproduced" \
  "$spec_valid" "$evidence_verified" \
  > /logs/verifier/reward.json
exit 0
