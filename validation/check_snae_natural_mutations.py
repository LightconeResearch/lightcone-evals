"""Compatibility entry point for the shared SNAE mutation checks."""

import runpy
from pathlib import Path

runpy.run_path(
    str(Path(__file__).with_name("check_snae_mutations.py")), run_name="__main__"
)
