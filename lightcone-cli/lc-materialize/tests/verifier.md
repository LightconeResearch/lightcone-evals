---
document_version: '0.3'
verifier:
  name: smoke-lc-materialize-verifier
  default_strategy: script
  strategies:
    script: { type: script, command: ./test.sh }
  rubric:
    combine: min  # all-or-nothing
    dimensions:
      output_value: { weight: 0.25, source: results/baseline/summary.txt }
      status_current: { weight: 0.25, source: lc status --json }
      check_passes: { weight: 0.25, source: lc materialize --check --json }
      manifest: { weight: 0.25, source: results/baseline/.summary.manifest.json }
  outputs:
    reward_text: /logs/verifier/reward.txt
    reward_json: /logs/verifier/reward.json
---

## verifier intent

A 1.0 shows: `lc` builds an output, records it current, and writes its manifest. Each check scores 0 or 1 and the reward is their minimum:

- `output_value`: results/baseline/summary.txt holds the expected value
- `status_current`: `lc status --json` records baseline/summary as current
- `check_passes`: `lc materialize --check --json` finds nothing to do
- `manifest`: the run manifest names the output and hashes summary.txt

The project is ready to run; the one thing the agent has to discover is that
`lc materialize` needs an allocated cluster (`lc compute launch`). A
`summary.txt` written by hand passes `output_value` and fails the other three:
only the engine writes the manifest and the run record `lc status` reads.
