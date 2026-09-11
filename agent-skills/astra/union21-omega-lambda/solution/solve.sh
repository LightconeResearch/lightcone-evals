#!/bin/bash
set -euo pipefail

# Scripted reference solution ("oracle"). Runs as root; helper files placed
# next to this script are available under /solution/.

PROJECT=/root/sn-cosmology

cp /solution/astra.yaml "$PROJECT/astra.yaml"
mkdir -p "$PROJECT/scripts"
cp /solution/scripts/*.py "$PROJECT/scripts/"

astra validate "$PROJECT/astra.yaml"

cd "$PROJECT"

python3 scripts/fit.py \
  --data data/SCPUnion2.1_mu_vs_z.txt \
  --covmat-nosys data/SCPUnion2.1_covmat_nosys.txt \
  --covmat-sys data/SCPUnion2.1_covmat_sys.txt \
  --covariance with_systematics \
  --magnitude-treatment marginalized \
  --output results/best_fit.json

python3 scripts/plot_hubble.py \
  --data data/SCPUnion2.1_mu_vs_z.txt \
  --fit results/best_fit.json \
  --output results/hubble_diagram.png

astra validate "$PROJECT/astra.yaml" --verify-evidence
