"""Real subprocess-backed verification tools.

These wrap pytest/ruff/mypy and return their actual output. The pipeline
uses these results as evidence directly, instead of asking an LLM to report
whether tests passed - self-reported verification is not verification.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CommandResult:
    command: str
    exit_code: int
    stdout: str
    stderr: str

    @property
    def ok(self) -> bool:
        return self.exit_code == 0

    @property
    def combined_output(self) -> str:
        return (self.stdout + self.stderr).strip()


def _run(cmd: list[str], cwd: Path) -> CommandResult:
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    return CommandResult(
        command=" ".join(cmd),
        exit_code=proc.returncode,
        stdout=proc.stdout,
        stderr=proc.stderr,
    )


def run_tests(product_dir: Path, module_name: str) -> CommandResult:
    return _run(
        [
            "python3",
            "-m",
            "pytest",
            f"tests/test_{module_name}.py",
            "-v",
            f"--cov=src.{module_name}",
            "--cov-report=term-missing",
        ],
        cwd=product_dir,
    )


def run_lint(product_dir: Path, module_name: str) -> CommandResult:
    return _run(["ruff", "check", f"src/{module_name}.py"], cwd=product_dir)


def run_typecheck(product_dir: Path, module_name: str) -> CommandResult:
    return _run(["mypy", "--strict", f"src/{module_name}.py"], cwd=product_dir)
