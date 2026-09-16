Exercise the execution lifecycle of the supplied Union2.1 analysis in
`/root/snae-build` using `lightcone-cli` (`lc`). The scientific scripts and
`astra.yaml` are complete. Preserve them, the four output contracts, and the
scientific methods except for the explicitly requested changes below.

Use `astra` for specification help and validation, and `lc --help` and its
subcommand help for execution. If an ASTRA skill is available, load it.
Declare the scripts' dependencies through `uv add`, which updates the locked
project environment. Commit edits before executing; `lc` requires a clean
tree and commits each output with its provenance. Never write outputs or
manifests yourself, invoke git-annex directly, or disable isolation.

Keep a handoff record outside the repository at `/root/snae-build-reports`.
For each named run below, save the unmodified stdout of
`lc materialize ... --json` as `<name>.json` and stderr as `<name>.stderr`.
After each run, tag its repository HEAD `eval/<name>`. The tags are historical
checkpoints; retain them and the history. Record the requested `*-ready` tags
immediately after committing the corresponding input edits, before running.
Do not store reports inside either project or create extra universes.

Perform these steps in order:

1. **targeted:** Materialize only `baseline/hubble_diagram` and its necessary
   dependency `best_fit`. Leave `residuals` and `catalog_summary` unbuilt.
2. **full:** Materialize the remaining outputs. Preserve the already built
   outputs and their run records.
3. **repeat:** Repeat the full materialization with no changes. Confirm no
   recipes run and no new commit is created.
4. **decision:** Change only `redshift_cut` in `universes/baseline.yaml` from
   `z_min_001` to `none`. Commit, tag `eval/decision-ready`, then materialize
   all outputs. The fit and figures must update; the independent
   `catalog_summary` must retain its existing run record.
5. **input:** Increase the distance modulus (third whitespace-separated
   column) of the first non-comment data row by exactly `0.05`. Preserve all
   other rows and values. Commit, tag `eval/input-ready`, then materialize all
   outputs. Both the analysis branch and the catalog fingerprint must update.
6. **failed:** Change `redshift_cut` back to `z_min_001`. Also append exactly
   ` && python -c 'import sys; sys.exit(23)'` to the `best_fit` recipe command
   in the spec. This deliberately fails after writing the fit. Commit and
   tag `eval/failure-ready`, then attempt full materialization. Save its
   nonzero exit code in `failed.exitcode` as well as the JSON and stderr, and
   tag `eval/failed`. The failed output must roll back to its previous bytes
   and manifest; downstream figures must not run or gain success records.
7. **recovered:** Remove only the deliberate failure suffix, preserving the
   changed input data and restored redshift cut. Commit and tag
   `eval/recovery-ready`, then materialize all outputs successfully. The fit
   and figures must update while `catalog_summary` remains untouched.
8. **clone:** Make a fresh `git clone --no-local --branch eval/recovery-ready`
   of the project at `/root/snae-reproduced`. Do not copy `.venv`, output
   files, or the annex store yourself. Initialize the clone with `lc init`
   to restore its locked environment. Remove the tracked prior output files
   and manifests with `git rm -r results/baseline`, commit, and tag
   `eval/clone-ready` in the clone. Then materialize all four outputs from
   the tracked inputs. This must retrieve inputs and reproduce the recovered
   outputs, rather than merely recognize unfetched output pointers as current.
   Save `clone.json` and `clone.stderr` in the same reports directory; create `eval/clone` in the clone. Compare the resulting output
   contents with the source project.
9. **published:** In the original project, declare `license = "CC-BY-4.0"`
   under `[project]` in `pyproject.toml`, commit, and materialize once more.
   The publication metadata must be generated without rerunning recipes.
   Leave both repositories clean and fully materialized. Save the original
   project's `lc materialize --check --json` output as `check.json`.

Skip interactive confirmations; this is an automated run.
