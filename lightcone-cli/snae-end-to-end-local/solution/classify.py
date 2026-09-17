#!/usr/bin/env python3
"""Classify the production boundary from declared demand and local cgroups."""

from __future__ import annotations

import json
import math
import os
import shutil
import subprocess
from pathlib import Path

import yaml

PROJECT = Path(os.environ.get("TASK_PROJECT_ROOT", "/root/snae"))


def available_cpus() -> int:
    cpu_max = Path("/sys/fs/cgroup/cpu.max")
    if cpu_max.is_file():
        quota, period = cpu_max.read_text().split()
        if quota != "max":
            return max(1, math.floor(int(quota) / int(period)))
    try:
        return max(1, len(os.sched_getaffinity(0)))
    except AttributeError:
        return max(1, os.cpu_count() or 1)


def available_memory_mb() -> float:
    memory_max = Path("/sys/fs/cgroup/memory.max")
    if memory_max.is_file():
        raw = memory_max.read_text().strip()
        if raw != "max":
            return int(raw) / 1_000_000
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemTotal:"):
            return int(line.split()[1]) / 1000
    raise RuntimeError("Could not determine local memory")


def memory_mb(value: str) -> float:
    value = value.strip().upper()
    if value.endswith("GB"):
        return float(value[:-2]) * 1000
    if value.endswith("MB"):
        return float(value[:-2])
    raise ValueError(value)


def main() -> None:
    request = json.loads((PROJECT / "execution-request.json").read_text())
    spec = yaml.safe_load((PROJECT / "astra.yaml").read_text())
    output = next(item for item in spec["outputs"] if item["id"] == request["output"])
    resources = output["recipe"]["resources"]
    cpus = available_cpus()
    memory = available_memory_mb()
    assert not os.environ.get("SLURM_JOB_ID")
    assert shutil.which("sbatch") is None
    status = json.loads(
        subprocess.check_output(["lc", "status", "--json"], cwd=PROJECT, text=True)
    )
    remaining = [o["output"] for o in status["outputs"] if o["status"] != "current"]
    assert "baseline/bootstrap_intervals" in remaining
    limiting = ["lifetime"]
    if resources["cpus"] > cpus:
        limiting.append("cpus")
    if memory_mb(resources["memory"]) > memory:
        limiting.append("memory")

    plan = {
        "output": request["output"],
        "universe": request["universe"],
        "environment": "local",
        "decision": "move-to-supported-environment",
        "limiting_resources": limiting,
        "next_environment": "supported-configured-slurm-site",
        "next_command": None,
        "remaining_outputs": remaining,
        "requested_resources": resources,
        "available_resources": {"cpus": cpus, "memory_mb": memory, "gpus": 0},
        "reason": (
            "This host has no Slurm submission tools, insufficient CPU/memory, and no "
            "session-independent allocation. Move the project to a supported Slurm "
            "site, request at least 8 CPUs, 8GB and 6h in a batch allocation, then "
            "materialize baseline/bootstrap_intervals inside that allocation. "
            "The site account and queue must be confirmed before a submission command "
            "can be given. Recipe resource annotations do not create an allocation."
        ),
    }
    (PROJECT / "execution-plan.json").write_text(
        json.dumps(plan, indent=2, sort_keys=True) + "\n"
    )


if __name__ == "__main__":
    main()
