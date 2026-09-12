# union21-omega-lambda-astra

The ASTRA-prompt tier of `union21-omega-lambda`.

Everything except the prompt is shared with the sibling task: `environment/`, `tests/` and `solution/` are relative symlinks into `../union21-omega-lambda/`, so there is one environment, one oracle and one verifier across both tasks.
What differs is this task's own `instruction.md`, which names ASTRA and says the choices belong in the spec, and its own `task.toml`, which states `[verifier.env] PROMPT_VARIANT = "astra"` and so selects the reward formula that also grades `spec_valid` and `evidence_verified`.

The instruction deliberately does not teach the ASTRA format — no `prior_insights`, `decisions:`, recipe syntax, output types, or CLI commands.
Teaching the format is the skill's job.

The third tier of the ablation is this same task run with the ASTRA skill installed:

```
harbor run -p agent-skills/astra/union21-omega-lambda-astra --skill <astra skill dir>
```

See `../union21-omega-lambda/README.md` for the rubric and `../union21-omega-lambda/tests/verifier.md` for the full rationale.
