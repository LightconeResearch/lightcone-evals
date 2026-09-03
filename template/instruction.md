Describe the task to the agent here. This is the only prompt the agent sees.

State what must be produced (exact paths), what must be preserved, and what must
NOT be done. Refer to files by absolute path inside the container (the project
usually lives under `/root/<project>`). Do not mention the verifier, the tests,
or the reward — the agent must not be told how it is scored.

Keep it realistic: an underspecified, user-like request exercises the stack the
way naive usage does; an exam-like checklist narrows the exploration that finds
failure modes. Choose deliberately.
