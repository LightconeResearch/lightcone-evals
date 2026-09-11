#!/bin/bash
set +e

# science_level is a single ordinal 0-3, not three independent dimensions:
# level 2 requires level 1's conditions, level 3 requires level 2's. Each
# level's pytest group therefore only checks its own INCREMENTAL condition
# (level 1's figure/fit check is not re-run inside level 2 or 3) and this
# script only advances the ladder while the previous rung held, so the
# nesting is enforced structurally rather than by weighting or re-checking.
#
# astra_spec_valid and astra_evidence_and_decisions are 0/1 flags measuring
# whether the agent reached for ASTRA at all (tier A of the ablation) or
# whether the plugin worked (tier C). They are folded into reward alongside
# science_level (see the reward formula below) but each is also reported as
# its own key, so "did the science" and "used ASTRA" stay individually
# legible even though they now combine into one number.

mkdir -p /logs/verifier

science_level=0
astra_spec_valid=0
astra_evidence_and_decisions=0

python3 -m pytest /tests/test_science_level_1_fit_and_figure.py -rA -v \
  > /logs/verifier/science-level-1.txt 2>&1
rc=$?
cat /logs/verifier/science-level-1.txt
if [ "$rc" -eq 0 ]; then
  science_level=1

  python3 -m pytest /tests/test_science_level_2_systematics_covariance.py -rA -v \
    > /logs/verifier/science-level-2.txt 2>&1
  rc=$?
  cat /logs/verifier/science-level-2.txt
  if [ "$rc" -eq 0 ]; then
    science_level=2

    python3 -m pytest /tests/test_science_level_3_paper_reproduced.py -rA -v \
      > /logs/verifier/science-level-3.txt 2>&1
    rc=$?
    cat /logs/verifier/science-level-3.txt
    if [ "$rc" -eq 0 ]; then
      science_level=3
    fi
  fi
fi

python3 -m pytest /tests/test_astra_spec_valid.py -rA -v \
  > /logs/verifier/astra-spec-valid.txt 2>&1
rc=$?
cat /logs/verifier/astra-spec-valid.txt
if [ "$rc" -eq 0 ]; then
  astra_spec_valid=1
fi

python3 -m pytest /tests/test_astra_evidence_and_decisions.py -rA -v \
  > /logs/verifier/astra-evidence-and-decisions.txt 2>&1
rc=$?
cat /logs/verifier/astra-evidence-and-decisions.txt
if [ "$rc" -eq 0 ]; then
  astra_evidence_and_decisions=1
fi

# Collecting the agent's astra.yaml, best_fit.json, and hubble_diagram.png
# for human review is task.toml's top-level `artifacts` job (declarative
# source -> destination entries, landing under
# jobs/<ts>/<trial>/artifacts/), not this script's -- this file is scoring
# only. See task.toml for why and where.

# reward folds science_level (0.6) and the two ASTRA flags (0.2 each) into
# one number, per instruction: instruction-following is what's being
# measured for now, so it belongs in reward. Each component stays reported
# individually below too, precisely so "did the science" and "used ASTRA"
# remain separately legible even though they combine into one score.
reward=$(python3 -c "print(f'{0.6 * (${science_level} / 3) + 0.2 * ${astra_spec_valid} + 0.2 * ${astra_evidence_and_decisions}:.2f}')")
printf '%s\n' "$reward" > /logs/verifier/reward.txt
printf '{"reward": %s, "science_level": %d, "astra_spec_valid": %d, "astra_evidence_and_decisions": %d}\n' \
  "$reward" "$science_level" "$astra_spec_valid" "$astra_evidence_and_decisions" \
  > /logs/verifier/reward.json
exit 0
