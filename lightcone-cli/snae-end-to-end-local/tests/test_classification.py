from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

PROJECT = Path(os.environ.get("TASK_PROJECT_ROOT", "/root/snae"))


def plan() -> dict:
    return json.loads((PROJECT / "execution-plan.json").read_text())


def test_plan_matches_supplied_schema() -> None:
    schema = json.loads((PROJECT / "execution-plan.schema.json").read_text())
    Draft202012Validator(schema).validate(plan())


def test_astra_is_valid_and_demand_is_complete() -> None:
    result = subprocess.run(
        # The pip-installed astra-tools==0.2.13 entry point is root-owned; the
        # uvx cache the agent uses is writable by the agent and must not grade.
        ["astra", "validate", str(PROJECT / "astra.yaml")],
        cwd=PROJECT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout
    spec = yaml.safe_load((PROJECT / "astra.yaml").read_text())
    output = next(item for item in spec["outputs"] if item["id"] == "bootstrap_intervals")
    resources = output["recipe"]["resources"]
    assert resources == {"cpus": 8, "memory": "8GB", "time_limit": "6h"}
    assert resources.get("gpus", 0) == 0


def test_plan_targets_exact_request() -> None:
    request = json.loads((PROJECT / "execution-request.json").read_text())
    result = plan()
    assert result["output"] == request["output"] == "bootstrap_intervals"
    assert result["universe"] == request["universe"] == "baseline"


def test_plan_recognizes_local_environment_without_slurm() -> None:
    result = plan()
    assert result["environment"] == "local"
    assert not os.environ.get("SLURM_JOB_ID")
    assert subprocess.run(["sh", "-c", "command -v sinfo"], check=False).returncode != 0


def test_plan_moves_work_instead_of_claiming_local_async() -> None:
    result = plan()
    assert result["decision"] == "move-to-supported-environment"
    assert result["next_environment"] == "supported-configured-slurm-site"
    # ``lc run --async`` is the right command *on the supported site*; what the
    # plan must not do is present it as something to run on this local host.
    next_command = result["next_command"]
    if next_command is not None and "lc run --async" in next_command:
        assert result["next_environment"] != "current-local-host"
        assert result["environment"] == "local"


def test_plan_accounts_for_session_lifetime() -> None:
    # The request must survive the session and local detached execution is
    # unsupported, so lifetime is limiting on every host. Whether cpus/memory
    # also limit depends on how the sandbox surfaces its cgroup limits (nproc
    # and free report the host, not the quota), so it is not required.
    limiting = set(plan()["limiting_resources"])
    assert "lifetime" in limiting
    assert plan()["reason"].strip()


def test_planning_did_not_execute_or_submit_work() -> None:
    jobs = PROJECT / ".lightcone" / "jobs"
    assert not (PROJECT / "results" / "baseline" / "bootstrap_intervals").exists()
    assert not jobs.exists() or not any(jobs.rglob("*"))
