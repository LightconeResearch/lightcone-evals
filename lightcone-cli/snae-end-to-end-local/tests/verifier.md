---
document_version: '2.0'
verifier:
  name: snae-end-to-end-local-verifier
  default_strategy: pytest
  strategies:
    pytest:
      type: script
      command: ./test.sh
  rubric:
    combine: weighted_sum
    dimensions:
      auditable_resource_estimation:
        weight: 0.4
        source: pytest
      local_synchronous_execution:
        weight: 0.3
        source: pytest
      unsupported_local_classification:
        weight: 0.3
        source: pytest
  outputs:
    reward_text: /logs/verifier/reward.txt
    reward_json: /logs/verifier/reward.json
---

## verifier intent

Verify the complete local workflow in three independently scored dimensions: auditable resource estimation for unresolved recipes, provenance-preserving synchronous materialization of only `best_fit`, and safe relocation planning for the oversized bootstrap boundary without local execution or submission.

The current engine contract uses one ZIP fit artifact, a sidecar manifest,
flat JSON status, Git/annex provenance and Linux Landlock isolation. All groups
require the protected scientific seed to remain intact and the final project
to be committed and clean. Independent resource probes use scratch files only.
