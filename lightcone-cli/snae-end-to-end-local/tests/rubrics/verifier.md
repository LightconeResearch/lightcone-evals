# End-to-End Local Workflow Rubric

The final reward is a weighted sum of three deterministic dimensions:

- **Auditable resource estimation (0.4):** all initially unresolved recipes have safe requests supported by schema-valid evidence and independent measurements, while the declared bootstrap request is preserved.
- **Local synchronous execution (0.3):** `best_fit` is scientifically coherent and provenance-tracked through Lightcone, while both figures and the bootstrap result remain unresolved and no asynchronous job record exists.
- **Unsupported local classification (0.3):** the schema-valid plan targets the exact bootstrap request, recognizes the local environment and its lifetime/capacity limits, and moves work to a supported configured Slurm site without executing or submitting it locally.

Each dimension receives either full credit or zero according to its deterministic test group.

The verifier checks the v2 artifact and provenance contract, including the
fit archive's JSON/CSV contents, hashes, declared filesystem isolation and the
single production execution commit. Protected references prevent changes to
the scientific methods, input data or production request. All groups require
a clean, committed final repository. These scores need a new v2 baseline.
