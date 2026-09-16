---
document_version: '0.1'
verifier:
  name: snae-natural-outcome-verifier
  default_strategy: script
  strategies:
    script: {type: script, command: ./test.sh}
  rubric:
    combine: weighted_sum
    dimensions:
      targeted_execution: {weight: 0.20, source: script}
      incremental_execution: {weight: 0.20, source: script}
      failure_recovery: {weight: 0.20, source: script}
      clone_reproduction: {weight: 0.20, source: script}
      publication_provenance: {weight: 0.20, source: script}
  outputs:
    reward_text: /logs/verifier/reward.txt
    reward_json: /logs/verifier/reward.json
---

The agent receives only the natural-language work request. It is not asked
for command transcripts, JSON reports, special tags, or grader checkpoints.
The verifier never runs recipes or completes work on the agent's behalf.

Image preparation records starting commits, requested analysis settings, input hashes,
and existing manifests in a root-only reference outside the agent workspace.
The grader compares the final projects with those starting states, inspecting
normal CLI status, output bytes, manifests and execution commits.

- Targeted execution: only the requested diagram and its fit are built; their
  declared data, decisions, isolation and provenance are correct.
- Incremental execution: the changed uncertainty model is respected and the independent
  catalog summary keeps its previous run record.
- Recovery: the execution defect is fixed, the corrected data is preserved,
  already successful work is reused, and previous results remain recoverable.
- Reproduction: the separate repository reconstructs its environment and has
  its own successful run records for all outputs, with matching output bytes.
- Publication: the original updated analysis has the requested license and
  tracked publication metadata covering all four actual products, without
  unnecessary recipe reruns.

All five dimensions are deterministic and equally weighted. This separate task
has different starting states and a different rubric from snae-build; compare
configurations within this task, not its raw score against snae-build's score.
