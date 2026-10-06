---
document_version: '0.3'
verifier:
  name: smoke-astra-author-verifier
  default_strategy: script
  strategies:
    script: { type: script, command: ./test.sh }
  rubric:
    combine: min  # all-or-nothing
    dimensions:
      spec_valid: { weight: 0.5, source: astra validate }
      declares_pipeline: { weight: 0.5, source: astra.resolve.resolve_outputs }
  outputs:
    reward_text: /logs/verifier/reward.txt
    reward_json: /logs/verifier/reward.json
---

## verifier intent

A 1.0 shows: a hand-written spec for a two-step pipeline validates and resolves. Each check scores 0 or 1 and the reward is their minimum:

- `spec_valid`: `astra validate` accepts the project
- `declares_pipeline`: astra's resolver finds raw_data → clean_data → fit_result, each with its script as recipe

`spec_valid` is the CLI's verdict on the whole project. `declares_pipeline` asks
astra's resolver (the default universe) whether the prompt's three ids are
wired raw_data -> clean_data -> fit_result with recipes running the two scripts.
