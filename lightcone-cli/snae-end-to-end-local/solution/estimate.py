#!/usr/bin/env python3
"""Measure the fixed SNAE recipes and write conservative resource envelopes."""

from __future__ import annotations

import json
import math
import os
import subprocess
import tempfile
import time
from datetime import UTC, datetime
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


def measure(command: list[str]) -> dict[str, object]:
    started = time.perf_counter()
    result = subprocess.run(
        ["/usr/bin/time", "-v", "lc", "run", *command],
        cwd=PROJECT,
        text=True,
        capture_output=True,
        check=False,
    )
    elapsed = time.perf_counter() - started
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)
    peak_rss_kb = None
    for line in result.stderr.splitlines():
        if "Maximum resident set size (kbytes):" in line:
            peak_rss_kb = int(line.rsplit(":", 1)[1].strip())
            break
    if peak_rss_kb is None:
        raise RuntimeError("/usr/bin/time did not report peak RSS")
    return {
        "command": ["lc", "run", *command],
        "elapsed_seconds": elapsed,
        "peak_rss_mb": peak_rss_kb / 1000,
        "exit_status": result.returncode,
    }


def request_for(sample: dict[str, object]) -> dict[str, object]:
    elapsed = float(sample["elapsed_seconds"])
    peak_rss_mb = float(sample["peak_rss_mb"])
    memory_mb = max(256, math.ceil((peak_rss_mb * 1.5) / 128) * 128)
    walltime_seconds = max(30, math.ceil((elapsed * 2.0) / 30) * 30)
    return {
        "cpus": 1,
        "memory": f"{memory_mb}MB",
        "time_limit": f"{walltime_seconds}s",
    }


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="snae-estimate-") as raw_tmp:
        tmp = Path(raw_tmp)
        fit_dir = tmp / "best_fit.zip"
        commands = {
            "best_fit": [
                "python",
                "scripts/fit.py",
                "--data",
                "data/SCPUnion2.1_mu_vs_z.txt",
                "--output",
                str(fit_dir),
                "--optimizer",
                "nelder_mead",
                "--error-model",
                "stat_and_sys",
                "--redshift-cut",
                "z_min_001",
            ],
            "hubble_diagram": [
                "python",
                "scripts/plot_hubble.py",
                "--data",
                "data/SCPUnion2.1_mu_vs_z.txt",
                "--fit",
                str(fit_dir),
                "--output",
                str(tmp / "hubble_diagram.png"),
            ],
            "residuals": [
                "python",
                "scripts/plot_residuals.py",
                "--data",
                "data/SCPUnion2.1_mu_vs_z.txt",
                "--fit",
                str(fit_dir),
                "--output",
                str(tmp / "residuals.png"),
            ],
        }
        samples = {name: measure(command) for name, command in commands.items()}

    spec = yaml.safe_load((PROJECT / "astra.yaml").read_text())
    output_defs = {output["id"]: output for output in spec["outputs"]}
    estimates = []
    for output_name, sample in samples.items():
        request = request_for(sample)
        output_defs[output_name]["recipe"]["resources"] = request
        estimates.append(
            {
                "output": output_name,
                "basis": "measured",
                "evidence": [sample],
                "model": "Fixed-size deterministic workload; upper envelope of one isolated run",
                "safety_factors": {"walltime": 2.0, "memory": 1.5},
                "request": request,
            }
        )

    (PROJECT / "astra.yaml").write_text(yaml.safe_dump(spec, sort_keys=False))
    record = {
        "schema_version": 1,
        "timestamp": datetime.now(UTC).isoformat(),
        "target": {
            "outputs": ["best_fit", "hubble_diagram", "residuals"],
            "universe": "baseline",
        },
        "environment": {
            "kind": "local",
            "cpus_available": available_cpus(),
            "memory_mb_available": available_memory_mb(),
            "gpus_available": 0,
        },
        "estimates": estimates,
    }
    evidence_path = PROJECT / ".lightcone" / "estimates.json"
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
