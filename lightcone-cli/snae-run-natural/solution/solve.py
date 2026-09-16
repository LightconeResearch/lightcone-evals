"""Oracle only; none of these instructions are supplied to the evaluated agent."""

import subprocess
from pathlib import Path

import yaml

ROOT = Path("/root/snae-natural")
FAILURE_SUFFIX = " && python -c 'import sys; sys.exit(23)'"


def run(root, *args):
    subprocess.run(args, cwd=root, check=True)


def commit(root, message):
    run(root, "git", "add", "-A")
    run(root, "git", "commit", "-qm", message)


new = ROOT / "new-analysis"
run(new, "uv", "add", "numpy", "scipy", "matplotlib")
commit(new, "Record the scientific dependencies")
run(new, "lc", "materialize", "baseline/hubble_diagram")
updated = ROOT / "updated-analysis"
run(updated, "lc", "materialize")
interrupted = ROOT / "interrupted-analysis"
path = interrupted / "astra.yaml"
spec = yaml.safe_load(path.read_text())
fit = next(o for o in spec["outputs"] if o["id"] == "best_fit")
assert fit["recipe"]["command"].endswith(FAILURE_SUFFIX)
fit["recipe"]["command"] = fit["recipe"]["command"][: -len(FAILURE_SUFFIX)]
path.write_text(yaml.safe_dump(spec, sort_keys=False))
commit(interrupted, "Repair the failing post-processing step")
run(interrupted, "lc", "materialize")
clone = ROOT / "reproduced-analysis"
run(ROOT, "git", "clone", "--no-local", str(updated), str(clone))
assert not (clone / ".venv").exists()
run(clone, "lc", "init", ".")
run(clone, "git", "rm", "-r", "results/baseline")
commit(clone, "Prepare to reproduce outputs from tracked inputs")
run(clone, "lc", "materialize")
path = updated / "pyproject.toml"
path.write_text(
    path.read_text().replace("[project]\n", '[project]\nlicense = "CC-BY-4.0"\n', 1)
)
commit(updated, "Declare the publication license")
run(updated, "lc", "materialize")
print(
    "Completed the requested diagram, uncertainty update, recovery, reproduction and publication."
)
