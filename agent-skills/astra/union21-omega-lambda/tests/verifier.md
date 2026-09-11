---
document_version: '0.3'
verifier:
  name: union21-omega-lambda-verifier
  default_strategy: pytest
  strategies:
    pytest:
      type: script
      command: ./test.sh
  rubric:
    combine: weighted_sum
    dimensions:
      spec_validity:
        weight: 0.2
        source: pytest
      analysis_executed:
        weight: 0.2
        source: pytest
      omega_lambda_value:
        weight: 0.2
        source: pytest
      omega_lambda_uncertainty:
        weight: 0.2
        source: pytest
      evidence_and_decision:
        weight: 0.2
        source: pytest
  outputs:
    reward_text: /logs/verifier/reward.txt
    reward_json: /logs/verifier/reward.json
---

## verifier intent

Five independently scored dimensions. `spec_validity` checks that
`astra.yaml` is schema- and semantically-valid and declares a data input, a
metric output, and a downstream figure output, each with a recipe command.
`analysis_executed` checks that the analysis actually ran — a
machine-readable best-fit artifact and a non-trivial, decodable
Hubble-diagram PNG exist somewhere under the project. `omega_lambda_value`
and `omega_lambda_uncertainty` are scored separately because they fail for
different reasons: the value tests whether the fit itself is right, the
uncertainty tests whether the agent noticed the statistical-vs-systematics
covariance distinction and switched to the systematics-inclusive matrix (its
uncertainty is ~0.030 against ~0.013 for statistical-only — recovering the
right central value with the wrong covariance passes `omega_lambda_value`
but fails `omega_lambda_uncertainty`). `evidence_and_decision` checks that
the paper's Omega_Lambda constraint was verified as evidence and that the
spec's `decisions:` block names the covariance choice with the
systematics-inclusive option selected.

The agent authors astra.yaml from scratch and chooses its own output layout,
so the last three dimensions never hardcode a file path or JSON key: they
glob every JSON/YAML file under the project (excluding `data/` and the spec
itself) and pattern-match on keys that look like an Omega_Lambda value or
its uncertainty (`_util.py`'s `_OMEGA_KEY`/`_SIGMA_KEY` regexes), and they
pattern-match decision option text for "systematic" versus "statistical"
rather than requiring specific IDs. What's checked strictly is the physics
(the recovered value and uncertainty must fall in narrow, paper-informed
windows) and the validation outcomes (`astra validate` and
`--verify-evidence` must both report full success). A task that guesses
wrong on covariance, skips the evidence quote, or never runs the analysis
fails on exactly the dimension that shows it, independent of the others.
