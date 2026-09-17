# SNAE end-to-end local v2.0

This task evaluates a local production workflow: estimate three unresolved
recipes, materialize only the baseline fit, then plan where an oversized
bootstrap request should run. It remains a structured resource-planning task;
the natural-language prompt comparison lives in `snae-run-natural` and `snae-build`.

## Current CLI compatibility

The image installs lightcone-cli from `main` by default and installs its exact
ASTRA dependency version, avoiding the former 0.2.13 dependency conflict.
The benchmark runner resolves the requested CLI ref once and pins all task
images to that SHA. Direct builds accept `LIGHTCONE_COMMIT` as an override.

The seed is an initialized Git/annex project with a locked Python environment.
The reference solution measures recipes with `lc run`, records conservative
resource envelopes, commits the definition and uses `lc materialize` for
production execution. It records and commits the final execution plan.

Current CLI outputs are individual files. The fit and bootstrap recipes now
package their JSON and CSV files into deterministic ZIP archives; figures are
PNG files. The numerical methods, data, decisions, 0.03 mag systematic floor
and production request (8 CPUs, 8 GB, 6 hours, 20,000 resamples) are unchanged.
The requested fit is `results/baseline/best_fit.zip`, accompanied by
`.best_fit.manifest.json`. The archive contains `best_fit.json` and
`fitted_model.csv`.

The local host has no scheduler. The plan must move production bootstrap work
to a configured Slurm site and explain the capacity/session limitations.
Resource annotations do not allocate compute. At the destination, an external
batch allocation must provide the requested resources before materialization;
the CLI does not supply the former `--async` submission interface. No bootstrap
execution or scheduler submission occurs in this task.

## Scoring and validation

The three binary dimensions retain their original weights:

| Dimension | Weight | Required evidence |
| --- | --- | --- |
| Auditable resource estimation | 0.4 | Valid resource annotations, schema-valid evidence, independently measured envelopes |
| Local synchronous execution | 0.3 | Coherent fit, current status, committed provenance and no unrequested production outputs |
| Unsupported local classification | 0.3 | Preserved production request and a schema-valid handoff plan |

The agent runs as an ordinary user; the verifier uses protected reference files
to check that the supplied scientific contract remains intact. Scratch resource
probes may generate temporary files, but only the fit may be materialized in
the production results. The final project must be committed and clean.

See [validation procedures](../../validation/README.md). In addition to a full
oracle run, seven mutation checks test rejection of missing estimate evidence,
unsupported GPU requests, corrupt fit bytes, forged provenance, unrequested
figures, a local execution decision and a reduced production resource request.

Version 2 changes the execution interface, artifact layout and verification
contract. Do not compare its scores directly with v1 baselines.
