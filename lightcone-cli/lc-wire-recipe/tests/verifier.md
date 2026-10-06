---
document_version: '0.3'
verifier:
  name: smoke-lc-wire-recipe-verifier
  default_strategy: script
  strategies:
    script: { type: script, command: ./test.sh }
  rubric:
    combine: min  # all-or-nothing
    dimensions:
      spec_valid: { weight: 0.2, source: astra validate }
      output_value: { weight: 0.2, source: results/baseline/summary.txt }
      status_current: { weight: 0.2, source: lc status --json }
      check_passes: { weight: 0.2, source: lc materialize --check --json }
      manifest: { weight: 0.2, source: results/baseline/.summary.manifest.json }
  outputs:
    reward_text: /logs/verifier/reward.txt
    reward_json: /logs/verifier/reward.json
---

## verifier intent

A 1.0 shows: a newly wired recipe validates and `lc` materializes it. Each check scores 0 or 1 and the reward is their minimum:

- `spec_valid`: `astra validate` accepts the project
- `output_value`: results/baseline/summary.txt holds the expected value
- `status_current`: `lc status --json` records baseline/summary as current
- `check_passes`: `lc materialize --check --json` finds nothing to do
- `manifest`: the run manifest hashes summary.txt and its recipe runs src/report.py

On top of lc-materialize, the agent has to give `summary` a `format:` and a
recipe command with `{inputs.moments}` and `{output}` that runs
`src/report.py`, and commit the spec before `lc materialize` will run. A
`summary.txt` written by hand fails `status_current`, `check_passes` and
`manifest`.
