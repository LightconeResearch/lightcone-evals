#!/bin/bash
set +e

# science_level is a single ordinal 0-3, not three independent dimensions:
# level 2 requires level 1's conditions, level 3 requires level 2's. Each
# level's pytest group therefore only checks its own INCREMENTAL condition
# (level 1's figure/fit check is not re-run inside level 2 or 3) and this
# script only advances the ladder while the previous rung held, so the
# nesting is enforced structurally rather than by weighting or re-checking.
#
# astra_spec_valid and astra_evidence_and_decisions are separate 0/1 flags,
# reported alongside but never summed into reward: they measure whether the
# agent reached for ASTRA at all (tier A of the ablation) or whether the
# plugin worked (tier C), not how good the science is.
#
# answer_found_elsewhere is a third diagnostic-only flag: the science rungs
# above read /root/sn-cosmology/results/best_fit.json strictly (the prompt
# names that exact path and its keys), so a fit filed anywhere else scores
# science_level 0 — correctly, since the prompt asked for it plainly. This
# flag re-runs the old glob+pattern search to tell "couldn't do the physics"
# apart from "did the physics, filed it elsewhere" without letting that
# search back into the score.

mkdir -p /logs/verifier

science_level=0
astra_spec_valid=0
astra_evidence_and_decisions=0
answer_found_elsewhere=0

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

answer_found_elsewhere=$(python3 /tests/check_answer_elsewhere.py)

cp /root/sn-cosmology/astra.yaml /logs/verifier/astra.yaml 2>/dev/null || true

reward=$(python3 -c "print(f'{${science_level} / 3:.2f}')")
printf '%s\n' "$reward" > /logs/verifier/reward.txt
printf '{"reward": %s, "science_level": %d, "astra_spec_valid": %d, "astra_evidence_and_decisions": %d, "answer_found_elsewhere": %d}\n' \
  "$reward" "$science_level" "$astra_spec_valid" "$astra_evidence_and_decisions" "$answer_found_elsewhere" \
  > /logs/verifier/reward.json
exit 0
