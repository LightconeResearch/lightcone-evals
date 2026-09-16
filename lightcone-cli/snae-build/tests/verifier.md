---
document_version: '0.4'
verifier:
  name: snae-build-execution-verifier
  default_strategy: script
  strategies:
    script:
      type: script
      command: ./test.sh
  rubric:
    combine: weighted_sum
    dimensions:
      targeted_execution: {weight: 0.15, source: script}
      full_execution: {weight: 0.15, source: script}
      idempotent_repeat: {weight: 0.10, source: script}
      selective_invalidation: {weight: 0.20, source: script}
      failure_recovery: {weight: 0.15, source: script}
      clone_reproduction: {weight: 0.15, source: script}
      publication_provenance: {weight: 0.10, source: script}
  outputs:
    reward_text: /logs/verifier/reward.txt
    reward_json: /logs/verifier/reward.json
---

The verifier checks the agent's completed execution lifecycle. It does not
run recipes or complete missing steps on the agent's behalf. Each dimension
is all-or-nothing; full success requires all seven dimensions.

Evidence combines CLI JSON reports with Git checkpoints, per-output run
commits, manifest/input/content hashes, untouched branches of the dependency
graph, and actual files in the source and reproduced projects. The output
set and scientific scripts are fixed against an image-owned reference.
Numerical fitting is supplied task code, not a scientific reasoning exam.

The injected failure occurs after the fit writes bytes. Its checkpoint must
retain the previous outputs and manifests, record no new success commit,
and show a failed fit plus blocked dependents. Recovery must execute the
changed decision, and the fresh clone must reproduce those output bytes.

Task version 0.2.0 replaces the old three-dimensional rubric. Do not compare
these scores with the stored v0.1 snae-build baseline; regenerate baselines
at the new task commit. The raw command reports and Git history are retained
in the verifier logs for diagnosis.
