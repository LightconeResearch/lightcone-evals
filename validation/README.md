# SNAE task validation

## Paired execution tasks

Check that the two conditions differ only in the tool-naming sentence and task
identity (requires Python 3.11 or newer):

```bash
python3 validation/check_snae_pair.py
```

Run each reference solution and verifier through Harbor, without model/API cost:

```bash
for task in snae-run-natural snae-build; do
  uvx --from harbor==0.22.0 harbor run \
    -p "lightcone-cli/$task" -a oracle -e docker \
    -o /tmp/snae-pair-oracle --job-name "$task" -q -y
done
```

Require reward 1.0, all five dimensions 1.0 and zero exceptions for each task.
The tasks' Docker default is CLI main. For a comparison run, lightcone-bench
resolves main to a SHA once and reuses it for both conditions, including the
oracle. Set TASK to the comma-separated pair, keep WITH_SKILLS=false, and use
the branch's TASKS_REF until these tasks are merged.

To verify rejection of incorrect outcomes, run the following from this
repository. Set CLI_SHA to a concrete CLI commit. Either task can be used
because their environment, solution and verifier files are identical:

```bash
docker build --build-arg LIGHTCONE_COMMIT="$CLI_SHA" \
  -t snae-execution-test lightcone-cli/snae-build/environment
docker run --rm -i --cpus 2 --memory 4g \
  -v "$PWD/lightcone-cli/snae-build/solution:/solution:ro" \
  -v "$PWD/lightcone-cli/snae-build/tests:/tests:ro" \
  -v "$PWD/validation:/validation:ro" \
  snae-execution-test bash -se <<'CHECK'
runuser -u agent -- bash /solution/solve.sh
bash /tests/test.sh
python3 -c 'import json; assert json.load(open("/logs/verifier/reward.json"))["reward"] == 1.0'
python3 /validation/check_snae_mutations.py
CHECK
```

The six mutations cover unrequested work, reversing the requested uncertainty
change, discarding the data correction, corrupt reproduced bytes, empty
publication metadata, and a replaced scientific script. Each must cause an
assertion failure, not a collection/import error. Mutated files are restored
after each check. The old check_snae_natural_mutations.py entry point redirects
to these shared checks.

The verifier observes CLI status, committed provenance and output bytes; it
never executes recipes on the agent's behalf. Agents and oracle solutions run
as the ordinary agent user. Only the root verifier can read the protected
reference state.

## End-to-end local v2

Run the complete CLI task folder through the same oracle selection used by CI:

```bash
uvx --from harbor==0.22.0 harbor run \
  -p lightcone-cli -a oracle -e docker \
  -o /tmp/snae-all-oracle --job-name all-cli -n 2 -q -y
```

Require three scored trials, no errors and reward 1.0 for each trial. The
end-to-end task has three dimensions; the prompt-comparison pair has five.
Check dimensions per task, since missing dimensions in heterogeneous Harbor
job means are not comparable. For reproducible comparisons, use the benchmark
runner's SHA resolution or replace `ARG LIGHTCONE_COMMIT=main` with a single
resolved SHA in temporary copies of all three tasks before running Harbor.

To test end-to-end rejection behavior in a disposable container:

```bash
docker build --build-arg LIGHTCONE_COMMIT="$CLI_SHA" \
  -t snae-e2e-test lightcone-cli/snae-end-to-end-local/environment
docker run --rm -i --cpus 2 --memory 4g \
  -v "$PWD/lightcone-cli/snae-end-to-end-local/solution:/solution:ro" \
  -v "$PWD/lightcone-cli/snae-end-to-end-local/tests:/tests:ro" \
  -v "$PWD/validation:/validation:ro" \
  snae-e2e-test bash -se <<'CHECK'
runuser -u agent -- bash /solution/solve.sh
bash /tests/test.sh
python3 -c 'import json; assert json.load(open("/logs/verifier/reward.json"))["reward"] == 1.0'
python3 /validation/check_snae_e2e_mutations.py
CHECK
```

The seven mutations cover estimate evidence, GPU requirements, fit bytes,
provenance, unrequested outputs, execution location and production resources.
Each must fail its relevant assertion. The checker commits tracked mutations
so a dirty tree alone cannot explain rejection, then restores each file and
the original commit. It is intended only for the disposable validation image.
The resource verifier runs independent scientific probes in temporary scratch
space; it never creates production results on the agent's behalf.
