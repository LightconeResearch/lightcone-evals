---
document_version: '0.3'
verifier:
  name: snae-build-verifier
  default_strategy: script
  strategies:
    script:
      type: script
      command: ./test.sh
  rubric:
    combine: weighted_sum
    dimensions:
      spec_valid:
        weight: 0.25
        source: script
      outputs_current:
        weight: 0.5
        source: script
      publication_ready:
        weight: 0.25
        source: script
  outputs:
    reward_text: /logs/verifier/reward.txt
    reward_json: /logs/verifier/reward.json
---

## verifier intent

Mirror lightcone-cli's own eval gate — `astra validate astra.yaml`,
`lc materialize --check` up to date with at least one output made, and
`ro-crate-metadata.json` present — as three deterministic dimensions, with
partial credit for how many of the declared outputs the agent actually got
to `current` (read from `lc status --json`). A spec that never gets its
formats declared scores 0 on the second and third dimensions, since the
engine cannot name a file to write.
