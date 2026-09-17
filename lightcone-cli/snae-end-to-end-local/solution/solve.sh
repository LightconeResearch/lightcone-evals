#!/bin/bash
set -euo pipefail

cd /root/snae
python3 /solution/estimate.py
uvx astra-tools@0.2.17 validate astra.yaml
git add astra.yaml
git commit -qm 'Record measured resource envelopes'
lc materialize baseline/best_fit
python3 /solution/classify.py
git add execution-plan.json
git commit -qm 'Record the production execution handoff'
