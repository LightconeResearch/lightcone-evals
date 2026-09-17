"""Initialize the supplied analysis and preserve a verifier-owned reference."""

import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path("/root/snae")
REFERENCE = Path("/opt/snae-e2e-reference")


def run(*args, cwd=None):
    return subprocess.run(
        args, cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


run("lc", "init", str(ROOT))
shutil.copytree(REFERENCE / "project", ROOT, dirs_exist_ok=True)
run("uv", "add", "numpy==2.2.6", "scipy==1.16.0", "matplotlib==3.10.3", cwd=ROOT)
run("git", "add", "-A", cwd=ROOT)
run("git", "commit", "-qm", "Seed the resource estimation and execution task", cwd=ROOT)
(REFERENCE / "state.json").write_text(
    json.dumps({"head": run("git", "rev-parse", "HEAD", cwd=ROOT)}) + "\n"
)
assert not run("git", "status", "--porcelain", cwd=ROOT)
