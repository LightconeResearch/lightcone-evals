from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import yaml
from conftest import REFERENCE, assert_unrequested_outputs_absent, validate_astra
from jsonschema import Draft202012Validator

PROJECT = Path(os.environ.get("TASK_PROJECT_ROOT", "/root/snae"))


def plan() -> dict:
    return json.loads((PROJECT / "execution-plan.json").read_text())


def test_plan_matches_supplied_schema() -> None:
    schema = json.loads((REFERENCE / "project/execution-plan.schema.json").read_text())
    Draft202012Validator(schema).validate(plan())


def test_astra_is_valid_and_demand_is_complete() -> None:
    validate_astra()
    spec = yaml.safe_load((PROJECT / "astra.yaml").read_text())
    output = next(
        item for item in spec["outputs"] if item["id"] == "bootstrap_intervals"
    )
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
    next_command = result["next_command"]
    if next_command is not None:
        assert "--async" not in next_command
        assert "lc run bootstrap_intervals" not in next_command
        assert result["next_environment"] != "current-local-host"


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
    assert_unrequested_outputs_absent()
    assert not jobs.exists() or not any(jobs.rglob("*"))
