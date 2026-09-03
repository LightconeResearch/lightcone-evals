#!/bin/bash
set -euo pipefail

python3 /solution/estimate.py
uvx astra-tools@0.2.13 validate /root/snae/astra.yaml
cd /root/snae
lc run best_fit --universe baseline
python3 /solution/classify.py
