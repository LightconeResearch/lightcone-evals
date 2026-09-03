---
document_version: '0.3'
verifier:
  name: CHANGE-ME-verifier
  default_strategy: pytest
  strategies:
    pytest:
      type: script
      command: ./test.sh
  rubric:
    combine: weighted_sum
    dimensions:
      dimension_one:
        weight: 1.0
        source: pytest
  outputs:
    reward_text: /logs/verifier/reward.txt
    reward_json: /logs/verifier/reward.json
---

## verifier intent

One paragraph: what the dimensions verify and why they are independent. Keep
each dimension deterministic — full credit or zero from its own test group.
