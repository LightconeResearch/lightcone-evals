Prepare the baseline analysis in `/root/snae` for repeatable production use with lightcone-cli. Add defensible CPU, memory, GPU, and walltime requirements to each recipe in `/root/snae/astra.yaml` that does not already declare them. Preserve the existing scientific methods, output formats, and declared production-bootstrap request.

Record an auditable basis for the new estimates at `/root/snae/.lightcone/estimates.json` using `/root/snae/estimate-record.schema.json`.

After estimation, reassess the current environment and materialize only the `best_fit` output for the `baseline` universe through the project's appropriate production execution interface. Preserve its provenance; do not materialize either figure.

Finally, reassess the production execution request in `/root/snae/execution-request.json` against the current environment and unresolved ASTRA graph. Write an immediately actionable plan to `/root/snae/execution-plan.json` using `/root/snae/execution-plan.schema.json`. Do not execute or submit `bootstrap_intervals`, and do not assume scheduler support that is unavailable from the current host.

Use the project's recorded environment and normal isolation and provenance mechanisms. Keep the supplied scripts, data, analysis choices and request schemas intact, and leave the final repository committed and clean. Resource measurements may use temporary scratch artifacts outside the production results.
