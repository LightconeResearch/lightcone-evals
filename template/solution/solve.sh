#!/bin/bash
set -euo pipefail

# Scripted reference solution ("oracle"). CI runs this instead of an agent and
# requires the verifier to score exactly 1.0 before any agent leg runs — it
# certifies the task and environment, at zero token cost. It runs as root.
# Helper files placed next to this script are available under /solution/.

echo "implement the reference solution here" >&2
exit 1
