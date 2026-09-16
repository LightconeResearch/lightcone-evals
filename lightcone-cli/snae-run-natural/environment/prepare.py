"""Prepare observable starting states; removed from the agent's image afterward."""

import hashlib
import json
import shutil
import subprocess
from pathlib import Path

import yaml

ROOT = Path("/root/snae-natural")
REFERENCE = Path("/opt/snae-natural-reference")
DATA = "data/SCPUnion2.1_mu_vs_z.txt"
FORMATS = {
    "best_fit": "json",
    "hubble_diagram": "png",
    "residuals": "png",
    "catalog_summary": "json",
}
FAILURE_SUFFIX = " && python -c 'import sys; sys.exit(23)'"
ROOT.mkdir(parents=True)


def run(*args, cwd=None, check=True):
    return subprocess.run(args, cwd=cwd, check=check, capture_output=True, text=True)


def git(root, *args):
    return run("git", *args, cwd=root).stdout.strip()


def commit(root, message):
    git(root, "add", "-A")
    git(root, "commit", "-qm", message)


def execute(root, *targets, fail=False):
    result = run("lc", "materialize", *targets, cwd=root, check=False)
    assert (result.returncode != 0) == fail, result.stdout + result.stderr
    return result


state = {}
for name in ("new-analysis", "updated-analysis", "interrupted-analysis"):
    root = ROOT / name
    run("lc", "init", str(root))
    shutil.copytree(REFERENCE / "seed", root, dirs_exist_ok=True)
    spec = yaml.safe_load((root / "astra.yaml").read_text())
    (root / "universes/baseline.yaml").write_text(
        yaml.safe_dump(
            {
                "id": "baseline",
                "decisions": {
                    name: decision["default"]
                    for name, decision in spec["decisions"].items()
                },
            },
            sort_keys=False,
        )
    )
    commit(root, "Import the supplied scientific analysis")
    previous = None
    if name != "new-analysis":
        run("uv", "add", "numpy", "scipy", "matplotlib", cwd=root)
        commit(root, "Record the scientific environment")
        execute(root)
        previous = git(root, "rev-parse", "HEAD")
    if name == "updated-analysis":
        path = root / "universes/baseline.yaml"
        universe = yaml.safe_load(path.read_text())
        universe["decisions"]["error_model"] = "stat_only"
        path.write_text(yaml.safe_dump(universe, sort_keys=False))
        commit(root, "Use statistical uncertainties only")
    if name == "interrupted-analysis":
        path = root / DATA
        lines = path.read_text().splitlines(keepends=True)
        for i, line in enumerate(lines):
            if line.strip() and not line.lstrip().startswith("#"):
                row = line.split()
                if float(row[1]) > 0.01:
                    row[2] = f"{float(row[2]) + 0.05:.8f}"
                    lines[i] = "\t".join(row) + "\n"
                    break
        path.write_text("".join(lines))
        spec_path = root / "astra.yaml"
        spec = yaml.safe_load(spec_path.read_text())
        next(o for o in spec["outputs"] if o["id"] == "best_fit")["recipe"][
            "command"
        ] += FAILURE_SUFFIX
        spec_path.write_text(yaml.safe_dump(spec, sort_keys=False))
        commit(root, "Correct the measurement and update the execution recipe")
        # A successful independent branch already reflects the corrected data.
        execute(root, "baseline/catalog_summary")
        before_failure = git(root, "rev-parse", "HEAD")
        previous_fit = (root / "results/baseline/best_fit.json").read_bytes()
        previous_manifest = (
            root / "results/baseline/.best_fit.manifest.json"
        ).read_bytes()
        result = execute(root, fail=True)
        assert git(root, "rev-parse", "HEAD") == before_failure
        assert (root / "results/baseline/best_fit.json").read_bytes() == previous_fit
        assert (
            root / "results/baseline/.best_fit.manifest.json"
        ).read_bytes() == previous_manifest
        # Raw failure evidence is outside the project and contains no tutorial.
        (ROOT / "previous-failure.log").write_text(result.stdout + result.stderr)
    state[name] = {
        "head": git(root, "rev-parse", "HEAD"),
        "previous_head": previous,
        "data_sha256": hashlib.sha256((root / DATA).read_bytes()).hexdigest(),
        "choices": yaml.safe_load((root / "universes/baseline.yaml").read_text())[
            "decisions"
        ],
        "manifests": {
            output: json.loads(
                (root / f"results/baseline/.{output}.manifest.json").read_text()
            )
            for output in FORMATS
            if (root / f"results/baseline/.{output}.manifest.json").exists()
        },
    }
    assert not git(root, "status", "--porcelain")
(REFERENCE / "state.json").write_text(json.dumps(state, indent=2) + "\n")
