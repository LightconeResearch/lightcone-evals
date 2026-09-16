"""Grade execution reports against committed Git checkpoints and actual artifacts.

No recipes are executed by the verifier and no agent outputs are repaired here.
The fixed reference is installed root-only in the image, outside the workspace.
"""

import hashlib
import json
import os
import subprocess
from pathlib import Path

import pytest
import yaml

ROOT = Path(os.environ.get("PROJECT", "/root/snae-build"))
REPORTS = Path(os.environ.get("REPORTS", "/root/snae-build-reports"))
CLONE = Path(os.environ.get("REPRO_PROJECT", "/root/snae-reproduced"))
REFERENCE = Path(os.environ.get("REFERENCE", "/opt/snae-reference"))
FORMATS = {
    "best_fit": "json",
    "hubble_diagram": "png",
    "residuals": "png",
    "catalog_summary": "json",
}
ALL = set(FORMATS)
ANALYSIS = ALL - {"catalog_summary"}
DATA = "data/SCPUnion2.1_mu_vs_z.txt"
FAILURE_SUFFIX = " && python -c 'import sys; sys.exit(23)'"


def command(*args, root=ROOT):
    result = subprocess.run(
        args, cwd=root, capture_output=True, text=True, timeout=90, check=False
    )
    assert result.returncode == 0, result.stderr or result.stdout
    return result.stdout


def git(*args, root=ROOT):
    return command("git", *args, root=root).strip()


def sha(stage, root=ROOT):
    return git("rev-parse", "--verify", f"refs/tags/eval/{stage}^{{commit}}", root=root)


def blob(stage, path, root=ROOT):
    result = subprocess.run(
        ["git", "show", f"{sha(stage, root)}:{path}"],
        cwd=root,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, f"{stage}: missing {path}: {result.stderr.decode()}"
    data = result.stdout
    # Both locked symlinks and unlocked annex pointers name the content key.
    if b"/annex/objects/" in data[:500] and len(data) < 32768:
        key = Path(data.decode().strip()).name
        location = git("annex", "contentlocation", key, root=root)
        return (root / location).read_bytes()
    return data


def artifact(stage, name, root=ROOT):
    return blob(stage, f"results/baseline/{name}.{FORMATS[name]}", root)


def manifest(stage, name, root=ROOT):
    return json.loads(blob(stage, f"results/baseline/.{name}.manifest.json", root))


def spec(stage, root=ROOT):
    return yaml.safe_load(blob(stage, "astra.yaml", root))


def choices(stage, root=ROOT):
    return yaml.safe_load(blob(stage, "universes/baseline.yaml", root))["decisions"]


def load_report(path):
    # lc currently streams recipe stdout ahead of its final JSON summary.
    # Keep the original stream and require a complete final report, not a
    # recipe's own JSON or an arbitrarily selected earlier success object.
    text = path.read_text()
    decoder = json.JSONDecoder()
    for offset, character in enumerate(text):
        if character != "{":
            continue
        try:
            data, end = decoder.raw_decode(text, offset)
        except json.JSONDecodeError:
            continue
        if (
            not text[end:].strip()
            and isinstance(data, dict)
            and {"ok", "up_to_date", "made", "failed", "blocked"} <= data.keys()
        ):
            return data
    raise AssertionError(f"{path}: no final materialization report")


def report(stage, expected_made, failed=(), blocked=()):
    data = load_report(REPORTS / f"{stage}.json")
    names = lambda items: {f"baseline/{name}" for name in items}
    assert len(data["made"]) == len(expected_made), data
    assert set(data["made"]) == names(expected_made), data
    assert set(data["failed"]) == names(failed), data
    assert set(data["blocked"]) == names(blocked), data
    assert data["ok"] is (not failed and not blocked), data
    if not failed and not expected_made:
        assert data["up_to_date"] is True
    return data


def same_outputs(before, after, names):
    for name in names:
        assert artifact(before, name) == artifact(after, name), name
        assert manifest(before, name) == manifest(after, name), name
        path = f"results/baseline/.{name}.manifest.json"
        assert git("log", "-1", "--format=%H", sha(before), "--", path) == git(
            "log", "-1", "--format=%H", sha(after), "--", path
        ), name


def produced_between(before, after, names, root=ROOT):
    """Check actual output commits, not just a claimed made[] list."""
    start, end = sha(before, root), sha(after, root)
    git("merge-base", "--is-ancestor", start, end, root=root)
    commits = git("rev-list", "--reverse", f"{start}..{end}", root=root).splitlines()
    assert len(commits) == len(names), (before, after, commits)
    found = []
    for commit in commits:
        message = git("show", "-s", "--format=%B", commit, root=root)
        assert "[DATALAD RUNCMD]" in message, message
        files = git(
            "diff-tree", "--no-commit-id", "--name-only", "-r", commit, root=root
        ).splitlines()
        output_names = [
            n for n in ALL if f"results/baseline/.{n}.manifest.json" in files
        ]
        assert len(output_names) == 1, files
        found.extend(output_names)
    assert len(found) == len(names) and set(found) == set(names)
    if "best_fit" in names:
        for downstream in {"hubble_diagram", "residuals"} & set(names):
            assert found.index("best_fit") < found.index(downstream)


def current(root):
    payload = json.loads(command("lc", "status", "--json", root=root))
    outputs = payload["outputs"]
    assert len(outputs) == len(ALL), outputs
    assert {o["output"] for o in outputs} == {f"baseline/{n}" for n in ALL}
    assert all(o["status"] == "current" for o in outputs), outputs
    assert not git("status", "--porcelain", root=root)


def assert_provenance(stage, names=ALL, root=ROOT):
    for name in names:
        m = manifest(stage, name, root)
        content = artifact(stage, name, root)
        assert m["data_version"] == "sha256:" + hashlib.sha256(content).hexdigest()
        assert m["output_id"] == name and m["universe_id"] == "baseline"
        assert m["recipe"] and m["env_version"] and m["lc_version"]
        assert m["hermeticity"]["fs"] == "declared"
        assert m["hermeticity"]["mechanism"] in {"landlock", "seatbelt"}
        git("merge-base", "--is-ancestor", m["git_sha"], sha(stage, root), root=root)
        inputs = {"union21": blob(stage, DATA, root)}
        if name in {"hubble_diagram", "residuals"}:
            inputs["best_fit"] = artifact(stage, "best_fit", root)
        assert m["input_versions"] == {
            k: "sha256:" + hashlib.sha256(v).hexdigest() for k, v in inputs.items()
        }
        assert m["decisions"] == (choices(stage, root) if name == "best_fit" else {})
        if FORMATS[name] == "png":
            assert content.startswith(b"\x89PNG\r\n\x1a\n") and len(content) > 1000


def test_targeted_execution():
    r = report("targeted", {"best_fit", "hubble_diagram"})
    assert r["made"] == ["baseline/best_fit", "baseline/hubble_diagram"]
    files = git("ls-tree", "-r", "--name-only", sha("targeted"), "results").splitlines()
    for name in ("residuals", "catalog_summary"):
        assert not any(name in Path(path).name for path in files)
    # The dependency setup is a user commit before the first engine commit.
    commits = git(
        "rev-list", "--reverse", f"{sha('seed')}..{sha('targeted')}"
    ).splitlines()
    assert len(commits) >= 3
    messages = [git("show", "-s", "--format=%B", c) for c in commits]
    assert sum("[DATALAD RUNCMD]" in msg for msg in messages) == 2
    assert_provenance("targeted", {"best_fit", "hubble_diagram"})


def test_full_execution_and_preserved_contract():
    report("full", {"residuals", "catalog_summary"})
    produced_between("targeted", "full", {"residuals", "catalog_summary"})
    same_outputs("targeted", "full", {"best_fit", "hubble_diagram"})
    reference = yaml.safe_load((REFERENCE / "astra.yaml").read_text())
    for stage in ("targeted", "full", "decision", "input", "recovered", "published"):
        assert spec(stage) == reference, f"{stage}: the fixed analysis contract changed"
        for script in (REFERENCE / "scripts").glob("*.py"):
            assert blob(stage, f"scripts/{script.name}") == script.read_bytes()
    assert blob("full", DATA) == (REFERENCE / DATA).read_bytes()
    assert choices("full") == {
        "optimizer": "nelder_mead",
        "error_model": "stat_and_sys",
        "redshift_cut": "z_min_001",
    }
    assert_provenance("full")


def test_idempotent_repeat():
    report("repeat", set())
    assert sha("repeat") == sha("full"), "no-op materialization created a commit"
    same_outputs("full", "repeat", ALL)


def test_decision_and_input_invalidation():
    report("decision", ANALYSIS)
    produced_between("decision-ready", "decision", ANALYSIS)
    same_outputs("repeat", "decision", {"catalog_summary"})
    assert choices("decision") == {**choices("full"), "redshift_cut": "none"}
    assert blob("decision", DATA) == blob("full", DATA)
    assert json.loads(artifact("decision", "best_fit"))["n_supernovae"] == 580
    assert artifact("decision", "best_fit") != artifact("full", "best_fit")
    report("input", ALL)
    produced_between("input-ready", "input", ALL)
    assert choices("input") == choices("decision")
    before = [
        line.split()
        for line in blob("decision", DATA).decode().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    after = [
        line.split()
        for line in blob("input", DATA).decode().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert len(before) == len(after) == 580
    assert before[1:] == after[1:]
    assert before[0][:2] == after[0][:2] and before[0][3:] == after[0][3:]
    assert float(after[0][2]) - float(before[0][2]) == pytest.approx(0.05, abs=1e-8)
    summary = json.loads(artifact("input", "catalog_summary"))
    assert summary == {
        "rows": 580,
        "sha256": hashlib.sha256(blob("input", DATA)).hexdigest(),
    }
    assert_provenance("decision")
    assert_provenance("input")


def test_failure_rollback_and_recovery():
    r = report(
        "failed", set(), failed={"best_fit"}, blocked={"hubble_diagram", "residuals"}
    )
    assert r["up_to_date"] is False
    assert int((REPORTS / "failed.exitcode").read_text()) != 0
    assert sha("failure-ready") == sha("failed"), "failed run created a success commit"
    failed_spec = spec("failed")
    fit = next(o for o in failed_spec["outputs"] if o["id"] == "best_fit")
    assert fit["recipe"]["command"].endswith(FAILURE_SUFFIX)
    fit["recipe"]["command"] = fit["recipe"]["command"][: -len(FAILURE_SUFFIX)]
    assert failed_spec == spec("input")
    assert choices("failed") == {**choices("input"), "redshift_cut": "z_min_001"}
    assert blob("failed", DATA) == blob("input", DATA)
    same_outputs("input", "failed", ALL)
    report("recovered", ANALYSIS)
    produced_between("recovery-ready", "recovered", ANALYSIS)
    same_outputs("input", "recovered", {"catalog_summary"})
    assert artifact("recovered", "best_fit") != artifact("input", "best_fit")
    assert_provenance("recovered")


def test_fresh_clone_reproduces():
    assert (CLONE / ".git").is_dir() and (CLONE / ".venv").is_dir()
    assert not (CLONE / ".venv").is_symlink()
    assert not (CLONE / ".git/objects/info/alternates").exists()
    origin = git("remote", "get-url", "origin", root=CLONE)
    assert Path(origin).resolve() == ROOT.resolve()
    assert sha("recovery-ready", CLONE) == sha("recovery-ready")
    report("clone", ALL)
    assert not git(
        "ls-tree",
        "-r",
        "--name-only",
        sha("clone-ready", CLONE),
        "results/baseline",
        root=CLONE,
    )
    git(
        "merge-base",
        "--is-ancestor",
        sha("recovery-ready"),
        sha("clone-ready", CLONE),
        root=CLONE,
    )
    produced_between("clone-ready", "clone", ALL, root=CLONE)
    for name in ALL:
        assert artifact("clone", name, CLONE) == artifact("recovered", name), name
        assert (
            CLONE / f"results/baseline/{name}.{FORMATS[name]}"
        ).read_bytes() == artifact("recovered", name)
    assert_provenance("clone", root=CLONE)
    current(CLONE)


def test_publication_and_final_state():
    report("published", set())
    same_outputs("recovered", "published", ALL)
    assert sha("published") == git("rev-parse", "HEAD")
    crate = json.loads((ROOT / "ro-crate-metadata.json").read_text())
    assert crate["@context"] and isinstance(crate["@graph"], list)
    ids = {item.get("@id") for item in crate["@graph"]}
    for name in ALL:
        assert f"results/baseline/{name}.{FORMATS[name]}" in ids
        assert (
            ROOT / f"results/baseline/{name}.{FORMATS[name]}"
        ).read_bytes() == artifact("published", name)
    check = json.loads((REPORTS / "check.json").read_text())
    assert (
        check["ok"]
        and check["up_to_date"]
        and set(check["current"]) == {f"baseline/{n}" for n in ALL}
    )
    # Verify the state independently through the public CLI; a claimed report is insufficient.
    current(ROOT)
