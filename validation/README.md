# snae-build execution validation

Run the reference solution and verifier through Harbor (no model/API cost):

```bash
uvx --from harbor==0.22.0 harbor run \
  -p lightcone-cli/snae-build -a oracle -e docker \
  -o /tmp/snae-oracle --job-name oracle -q -y
```

Require `reward == 1.0`, all seven dimensions equal to 1.0, and zero
exceptions. This is the same oracle gate required by lightcone-bench.
The task's direct Docker default is CLI main; the benchmark runner instead
resolves main to a SHA before building and records the SHA in trial context.

To test that the verifier rejects incorrect outcomes, run the following
from this repository. Pick a concrete CLI commit for `CLI_SHA` so repeat
builds use the same code:

```bash
docker build --build-arg LIGHTCONE_COMMIT="$CLI_SHA" \
  -t snae-execution-test lightcone-cli/snae-build/environment
docker run --rm --cpus 2 --memory 4g \
  -v "$PWD/lightcone-cli/snae-build/solution:/solution:ro" \
  -v "$PWD/lightcone-cli/snae-build/tests:/tests:ro" \
  -v "$PWD/validation:/validation:ro" \
  snae-execution-test bash -c \
  'bash /solution/solve.sh && bash /tests/test.sh && python3 -c '\''import json; assert json.load(open("/logs/verifier/reward.json"))["reward"] == 1.0'\'' && python3 /validation/check_snae_mutations.py'
```

The eight mutations cover unrequested work, non-idempotent reruns, needless
rebuilds of independent outputs, false success after failure, a missing
nonzero exit code, corrupt reproduced bytes, empty publication metadata,
and a forged no-op checkpoint. Each must cause an assertion failure, not a
collection/import error. Mutated files and tags are restored after each test.

The verifier preserves raw command stdout. The current CLI can stream a
recipe's stdout before its own JSON summary, so it extracts the final
complete materialization report rather than interpreting recipe output as
the report. Scores are also checked against committed history and bytes.

The supplied reference under `/opt/snae-reference` is root-only. Ordinary
agents can write the source project, reports directory and initially empty
clone directory, but cannot change that reference. The oracle and verifier
run as root, matching the Harbor task contract.
