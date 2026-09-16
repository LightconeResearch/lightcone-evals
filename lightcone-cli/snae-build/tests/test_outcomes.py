"""Observe work outcomes without requiring any agent-authored tags or reports."""

import hashlib
import json
import subprocess
from pathlib import Path

import tomllib
import yaml

ROOT = Path("/root/snae-natural")
REFERENCE = Path("/opt/snae-natural-reference")
FORMATS = {
    "best_fit": "json",
    "hubble_diagram": "png",
    "residuals": "png",
    "catalog_summary": "json",
}
ALL = set(FORMATS)
ANALYSIS = ALL - {"catalog_summary"}
DATA = "data/SCPUnion2.1_mu_vs_z.txt"


def execute(root, *args):
    result = subprocess.run(
        args, cwd=root, text=True, capture_output=True, timeout=60, check=False
    )
    assert result.returncode == 0, result.stderr or result.stdout
    return result.stdout.strip()


def git(root, *args):
    return execute(root, "git", *args)


def initial(name):
    return json.loads((REFERENCE / "state.json").read_text())[name]


def digest(content):
    return "sha256:" + hashlib.sha256(content).hexdigest()


def manifest(root, name):
    return json.loads((root / f"results/baseline/.{name}.manifest.json").read_text())


def artifact(root, name):
    return (root / f"results/baseline/{name}.{FORMATS[name]}").read_bytes()


def producer(root, name):
    return git(
        root,
        "log",
        "-1",
        "--format=%H",
        "--",
        f"results/baseline/.{name}.manifest.json",
    )


def assert_contract(root, state):
    reference = yaml.safe_load((REFERENCE / "seed/astra.yaml").read_text())
    assert yaml.safe_load((root / "astra.yaml").read_text()) == reference
    for path in (REFERENCE / "seed/scripts").glob("*.py"):
        assert (root / "scripts" / path.name).read_bytes() == path.read_bytes()
    assert (
        hashlib.sha256((root / DATA).read_bytes()).hexdigest() == state["data_sha256"]
    )
    universes = sorted((root / "universes").glob("*.yaml"))
    assert [p.name for p in universes] == ["baseline.yaml"]
    assert yaml.safe_load(universes[0].read_text())["decisions"] == state["choices"]
    assert not git(root, "status", "--porcelain"), (
        f"{root}: unfinished repository edits"
    )
    git(root, "merge-base", "--is-ancestor", state["head"], "HEAD")
    if state["previous_head"]:
        git(root, "merge-base", "--is-ancestor", state["previous_head"], "HEAD")


def assert_materialized(root, names, state):
    payload = json.loads(execute(root, "lc", "status", "--json"))
    assert len(payload["outputs"]) == len(ALL)
    assert {o["output"] for o in payload["outputs"]} == {f"baseline/{n}" for n in ALL}
    assert {o["output"] for o in payload["outputs"] if o["status"] == "current"} == {
        f"baseline/{n}" for n in names
    }
    for name in names:
        content = artifact(root, name)
        m = manifest(root, name)
        assert m["output_id"] == name and m["universe_id"] == "baseline"
        assert m["data_version"] == digest(content)
        assert m["recipe"] and m["env_version"] and m["lc_version"]
        assert m["hermeticity"]["fs"] == "declared"
        assert m["hermeticity"]["mechanism"] in {"landlock", "seatbelt"}
        inputs = {"union21": (root / DATA).read_bytes()}
        if name in {"hubble_diagram", "residuals"}:
            inputs["best_fit"] = artifact(root, "best_fit")
        assert m["input_versions"] == {
            key: digest(value) for key, value in inputs.items()
        }
        assert m["decisions"] == (state["choices"] if name == "best_fit" else {})
        recorded = producer(root, name)
        assert "[DATALAD RUNCMD]" in git(root, "show", "-s", "--format=%B", recorded)
        git(root, "merge-base", "--is-ancestor", m["git_sha"], recorded)
        if FORMATS[name] == "png":
            assert content.startswith(b"\x89PNG\r\n\x1a\n") and len(content) > 1000
    if "best_fit" in names:
        result = json.loads(artifact(root, "best_fit"))
        rows = [
            line.split()
            for line in (root / DATA).read_text().splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        ]
        n = sum(
            state["choices"]["redshift_cut"] == "none" or float(row[1]) > 0.01
            for row in rows
        )
        assert result["n_supernovae"] == n
        for key in ("optimizer", "error_model", "redshift_cut"):
            assert result[key] == state["choices"][key]


def assert_run_set(root, start, expected):
    commits = git(root, "rev-list", "--reverse", f"{start}..HEAD").splitlines()
    made = []
    for commit in commits:
        message = git(root, "show", "-s", "--format=%B", commit)
        if "[DATALAD RUNCMD]" not in message:
            continue  # Setup, repair, and publication commits are legitimate.
        paths = git(
            root, "diff-tree", "--no-commit-id", "--name-only", "-r", commit
        ).splitlines()
        names = [n for n in ALL if f"results/baseline/.{n}.manifest.json" in paths]
        assert len(names) == 1, paths
        made.extend(names)
    assert len(made) == len(expected) and set(made) == set(expected), made
    if "best_fit" in expected:
        for name in ("hubble_diagram", "residuals"):
            if name in expected:
                assert made.index("best_fit") < made.index(name)


def assert_independent_output_reused(root, state):
    assert manifest(root, "catalog_summary") == state["manifests"]["catalog_summary"]
    path = "results/baseline/.catalog_summary.manifest.json"
    assert producer(root, "catalog_summary") == git(
        root, "log", "-1", "--format=%H", state["head"], "--", path
    )


def test_targeted_execution():
    root = ROOT / "new-analysis"
    state = initial("new-analysis")
    assert_contract(root, state)
    assert_materialized(root, {"best_fit", "hubble_diagram"}, state)
    assert_run_set(root, state["head"], {"best_fit", "hubble_diagram"})
    for name in ("residuals", "catalog_summary"):
        for path in (
            root / f"results/baseline/{name}.{FORMATS[name]}",
            root / f"results/baseline/.{name}.manifest.json",
        ):
            assert not path.exists() and not path.is_symlink(), (
                f"unrequested output: {path}"
            )


def test_incremental_execution():
    root = ROOT / "updated-analysis"
    state = initial("updated-analysis")
    assert_contract(root, state)
    assert_materialized(root, ALL, state)
    assert_run_set(root, state["head"], ANALYSIS)
    assert_independent_output_reused(root, state)


def test_failure_recovery():
    root = ROOT / "interrupted-analysis"
    state = initial("interrupted-analysis")
    assert_contract(root, state)
    assert_materialized(root, ALL, state)
    assert_run_set(root, state["head"], ANALYSIS)
    assert_independent_output_reused(root, state)
    assert (
        manifest(root, "best_fit")["input_versions"]["union21"]
        != state["manifests"]["best_fit"]["input_versions"]["union21"]
    )
    # The previously successful outputs remain recoverable through Git/annex.
    for name in ALL:
        result = subprocess.run(
            [
                "git",
                "show",
                f"{state['previous_head']}:results/baseline/{name}.{FORMATS[name]}",
            ],
            cwd=root,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0
        key = Path(result.stdout.decode().strip()).name
        if b"/annex/objects/" in result.stdout:
            assert (root / git(root, "annex", "contentlocation", key)).is_file()


def test_clone_reproduction():
    root = ROOT / "reproduced-analysis"
    source = ROOT / "updated-analysis"
    state = initial("updated-analysis")
    assert (root / ".git").is_dir() and (root / ".venv").is_dir()
    assert not (root / ".venv").is_symlink()
    assert not (root / ".git/objects/info/alternates").exists()
    origin = git(root, "remote", "get-url", "origin").removeprefix("file://")
    assert Path(origin).resolve() == source.resolve()
    assert_contract(root, state)
    assert_materialized(root, ALL, state)
    for name in ALL:
        assert artifact(root, name) == artifact(source, name), name
        # A copied or merely fetched source output is not a reproduction.
        commit = producer(root, name)
        result = subprocess.run(
            ["git", "cat-file", "-e", f"{commit}^{{commit}}"],
            cwd=source,
            capture_output=True,
            check=False,
        )
        assert result.returncode != 0, f"{name}: still uses a source run record"
        assert manifest(root, name)["git_remote"].removeprefix("file://") == str(source)


def test_publication_provenance():
    root = ROOT / "updated-analysis"
    state = initial("updated-analysis")
    assert_contract(root, state)
    assert_materialized(root, ALL, state)
    project = tomllib.loads((root / "pyproject.toml").read_text())["project"]
    assert project["license"] == "CC-BY-4.0"
    path = "ro-crate-metadata.json"
    crate = json.loads((root / path).read_text())
    assert crate["@context"] and isinstance(crate["@graph"], list)
    ids = {item.get("@id") for item in crate["@graph"]}
    assert all(f"results/baseline/{n}.{FORMATS[n]}" in ids for n in ALL)
    assert json.loads(git(root, "show", f"HEAD:{path}")) == crate
    assert_run_set(root, state["head"], ANALYSIS)
