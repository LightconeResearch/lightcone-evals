#!/bin/bash
set -euo pipefail

# Scripted reference solution ("oracle"). Runs as root; helper files placed
# next to this script are available under /solution/.

# PROJECT has to be a literal: it is where contract.json itself lives, so
# nothing can derive it from the contract file it is used to find. It must
# agree with the Dockerfile's COPY/WORKDIR destination; the check below
# catches drift between them and contract.json's own project_root value.
PROJECT=/root/sn-cosmology

cp /solution/astra.yaml "$PROJECT/astra.yaml"
mkdir -p "$PROJECT/scripts"
cp /solution/scripts/*.py "$PROJECT/scripts/"

astra validate "$PROJECT/astra.yaml"

cd "$PROJECT"

contract_project_root=$(python3 -c "import json; print(json.load(open('contract.json'))['project_root'])")
if [ "$contract_project_root" != "$PROJECT" ]; then
  echo "ERROR: contract.json's project_root ('$contract_project_root') disagrees with solve.sh's PROJECT ('$PROJECT')" >&2
  exit 1
fi

best_fit_path=$(python3 -c "import json; print(json.load(open('contract.json'))['best_fit_path'])")
figure_path=$(python3 -c "import json; print(json.load(open('contract.json'))['figure_path'])")

python3 scripts/fit.py \
  --data data/SCPUnion2.1_mu_vs_z.txt \
  --covmat-nosys data/SCPUnion2.1_covmat_nosys.txt \
  --covmat-sys data/SCPUnion2.1_covmat_sys.txt \
  --covariance with_systematics \
  --magnitude-treatment marginalized \
  --output "$best_fit_path"

python3 scripts/plot_hubble.py \
  --data data/SCPUnion2.1_mu_vs_z.txt \
  --fit "$best_fit_path" \
  --output "$figure_path"

astra validate "$PROJECT/astra.yaml" --verify-evidence
