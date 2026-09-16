"""Reference execution of the public lifecycle instructions; no direct output writes."""

import os
import subprocess
from pathlib import Path

import yaml

ROOT = Path(os.environ.get("PROJECT", "/root/snae-build"))
REPORTS = Path(os.environ.get("REPORTS", "/root/snae-build-reports"))
CLONE = Path(os.environ.get("REPRO_PROJECT", "/root/snae-reproduced"))
REPORTS.mkdir(parents=True, exist_ok=True)


def run(*args, cwd=ROOT):
    return subprocess.run(args, cwd=cwd, text=True, check=True)


def tag(name, cwd=ROOT):
    run("git", "tag", f"eval/{name}", cwd=cwd)


def commit(message):
    run("git", "add", "-A")
    run("git", "commit", "-qm", message)


def materialize(name, *targets, cwd=ROOT, fail=False):
    with (
        (REPORTS / f"{name}.json").open("w") as stdout,
        (REPORTS / f"{name}.stderr").open("w") as stderr,
    ):
        result = subprocess.run(
            ["lc", "materialize", *targets, "--json"],
            cwd=cwd,
            stdout=stdout,
            stderr=stderr,
            check=False,
        )
    if fail:
        assert result.returncode != 0, (
            "deliberate recipe failure unexpectedly succeeded"
        )
        (REPORTS / "failed.exitcode").write_text(str(result.returncode) + "\n")
    else:
        assert result.returncode == 0, (REPORTS / f"{name}.stderr").read_text()
    tag(name, cwd)


def redshift(value):
    path = ROOT / "universes/baseline.yaml"
    spec = yaml.safe_load(path.read_text())
    spec["decisions"]["redshift_cut"] = value
    path.write_text(yaml.safe_dump(spec, sort_keys=False))


run("uv", "add", "numpy", "scipy", "matplotlib")
commit("Declare the supplied recipes dependencies")
materialize("targeted", "baseline/hubble_diagram")
materialize("full")
materialize("repeat")
redshift("none")
commit("Use all redshifts")
tag("decision-ready")
materialize("decision")
path = ROOT / "data/SCPUnion2.1_mu_vs_z.txt"
lines = path.read_text().splitlines(keepends=True)
for i, line in enumerate(lines):
    if line.strip() and not line.lstrip().startswith("#"):
        columns = line.split()
        columns[2] = f"{float(columns[2]) + 0.05:.8f}"
        lines[i] = "\t".join(columns) + "\n"
        break
path.write_text("".join(lines))
commit("Update the first distance modulus")
tag("input-ready")
materialize("input")
redshift("z_min_001")
path = ROOT / "astra.yaml"
original = path.read_text()
spec = yaml.safe_load(original)
fit = next(o for o in spec["outputs"] if o["id"] == "best_fit")
fit["recipe"]["command"] += " && python -c 'import sys; sys.exit(23)'"
path.write_text(yaml.safe_dump(spec, sort_keys=False))
commit("Inject the requested post-write failure")
tag("failure-ready")
materialize("failed", fail=True)
path.write_text(original)
commit("Remove the deliberate failure")
tag("recovery-ready")
materialize("recovered")
run(
    "git",
    "clone",
    "--no-local",
    "--branch",
    "eval/recovery-ready",
    str(ROOT),
    str(CLONE),
)
assert not (CLONE / ".venv").exists()
run("lc", "init", ".", cwd=CLONE)
run("git", "rm", "-r", "results/baseline", cwd=CLONE)
run(
    "git",
    "commit",
    "-qm",
    "Prepare a clean reproduction from tracked inputs",
    cwd=CLONE,
)
tag("clone-ready", CLONE)
materialize("clone", cwd=CLONE)
path = ROOT / "pyproject.toml"
path.write_text(
    path.read_text().replace("[project]\n", '[project]\nlicense = "CC-BY-4.0"\n', 1)
)
commit("Declare the publication license")
materialize("published")
with (REPORTS / "check.json").open("w") as stdout:
    subprocess.run(
        ["lc", "materialize", "--check", "--json"], cwd=ROOT, stdout=stdout, check=True
    )
