#!/bin/bash
# Re-score finished trials with the CURRENT verifier, without re-running them.
#
#   scripts/rescore.sh jobs/sweep-sonnet-C/sweep-sonnet-C/BC__WA2D3CQ ...
#   scripts/rescore.sh jobs/sweep-luna-*/*/*/
#
# A Harbor trial dir keeps the agent's work products under artifacts/ —
# astra.yaml, best_fit.json, hubble_diagram.png (task.toml's `artifacts`
# block collects them). That is everything this verifier reads, so a rescore
# is just: stage those three files into a fresh container at the paths the
# contract names, run tests/test.sh against them, and keep the output.
#
# Results land in <trial_dir>/verifier-v3/. Nothing already in the trial dir
# is touched: verifier/ (Harbor's own collection from the live run) and any
# earlier verifier-v2/ are left exactly as they were.
#
# The verifier grades every trial with the same formula, so no tier has to be
# plumbed in. The trial-name prefix (A__* ran union21-omega-lambda, BC__* ran
# union21-omega-lambda-astra) is used only to label the summary line.
#
# Requires the task image to exist locally; build it with
#   docker build -t union21-env:v2 environment/
# from the task root if it does not.

set -uo pipefail

TASK_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE="${UNION21_IMAGE:-union21-env:v2}"
PROJECT=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['project_root'])" \
  "$TASK_ROOT/environment/project/contract.json")
BEST_FIT=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['best_fit_path'])" \
  "$TASK_ROOT/environment/project/contract.json")
FIGURE=$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['figure_path'])" \
  "$TASK_ROOT/environment/project/contract.json")

if [ "$#" -eq 0 ]; then
  echo "usage: $0 <trial_dir> [trial_dir...]" >&2
  exit 2
fi

if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
  echo "image '$IMAGE' not found; build it with: docker build -t $IMAGE $TASK_ROOT/environment/" >&2
  exit 2
fi

failures=0

for trial_dir in "$@"; do
  trial_dir="${trial_dir%/}"
  trial=$(basename "$trial_dir")

  if [ ! -d "$trial_dir/artifacts" ]; then
    echo "SKIP  $trial_dir  (no artifacts/ — the trial never got that far)"
    continue
  fi

  case "$trial" in
    A__*)  label=baseline ;;
    BC__*) label=astra ;;
    *)     label=unlabelled ;;
  esac

  out_dir="$trial_dir/verifier-v3"
  rm -rf "$out_dir"
  mkdir -p "$out_dir"

  docker run --rm \
    -v "$TASK_ROOT/tests":/tests:ro \
    -v "$(cd "$trial_dir/artifacts" && pwd)":/artifacts:ro \
    -v "$(cd "$out_dir" && pwd)":/out \
    "$IMAGE" \
    bash -c "
      set -u
      mkdir -p /logs/verifier '$PROJECT/$(dirname "$BEST_FIT")' '$PROJECT/$(dirname "$FIGURE")'
      [ -f /artifacts/astra.yaml ]        && cp /artifacts/astra.yaml '$PROJECT/astra.yaml'
      [ -f /artifacts/best_fit.json ]     && cp /artifacts/best_fit.json '$PROJECT/$BEST_FIT'
      [ -f /artifacts/hubble_diagram.png ] && cp /artifacts/hubble_diagram.png '$PROJECT/$FIGURE'
      bash /tests/test.sh >/logs/verifier/test-stdout.txt 2>&1
      cp -a /logs/verifier/. /out/
    " >/dev/null 2>&1

  if [ ! -f "$out_dir/reward.json" ]; then
    echo "FAIL  $trial_dir  (verifier produced no reward.json)" >&2
    failures=$((failures + 1))
    continue
  fi

  python3 - "$trial_dir" "$out_dir" "$label" <<'PY'
import json, sys
trial_dir, out_dir, label = sys.argv[1], sys.argv[2], sys.argv[3]
reward = json.load(open(f"{out_dir}/reward.json"))
details = json.load(open(f"{out_dir}/details.json"))
sigma = details["omega_lambda_err"]
omega = details["omega_lambda"]
print(
    f"{reward['reward']:>5.2f}  {label:<11} "
    f"deliv={reward['deliverables']} "
    f"oL={reward['omega_lambda_score']:.2f} err={reward['omega_lambda_err_score']:.2f} "
    f"spec={reward['spec_valid']} ev={reward['evidence_verified']}  "
    f"omega={omega if omega is None else round(omega, 4)} "
    f"sigma={sigma if sigma is None else round(sigma, 4)}  {trial_dir}"
)
PY
done

exit $(( failures > 0 ))
