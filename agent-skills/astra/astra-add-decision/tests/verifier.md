---
document_version: '0.3'
verifier:
  name: smoke-astra-add-decision-verifier
  default_strategy: script
  strategies:
    script: { type: script, command: ./test.sh }
  rubric:
    combine: min  # all-or-nothing
    dimensions:
      spec_valid: { weight: 0.333, source: astra validate }
      decision_declared: { weight: 0.333, source: astra.helpers.get_decisions }
      universe_resolves: { weight: 0.333, source: astra universe check + astra.resolve }
  outputs:
    reward_text: /logs/verifier/reward.txt
    reward_json: /logs/verifier/reward.json
---

## verifier intent

A 1.0 shows: a new decision and universe validate, and the universe reaches the recipe. Each check scores 0 or 1 and the reward is their minimum:

- `spec_valid`: `astra validate` accepts the spec and every universe
- `decision_declared`: fit_model has options linear and quadratic, default linear
- `universe_resolves`: universes/quadratic.yaml checks, and fit_result's recipe takes {decisions.fit_model}

The starting project already validates with an empty `baseline` universe, so
adding `fit_model` without updating `baseline` makes `spec_valid` fail
(MISSING_DECISION): the guide's "a new decision touches every universe" rule.
`universe_resolves` asks the CLI whether the new universe is legal and astra's
resolver whether it actually reaches the fit recipe.
