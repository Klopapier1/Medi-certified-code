"""The 8-stage pipeline. Product-agnostic: everything here operates on a
ProductSpec and the standard requirements/design/src/tests/evidence layout -
nothing here may reference a specific product by name.
"""

from __future__ import annotations

from . import evidence, roles, tools
from .client import LLMClient
from .config import ProductSpec

SIGNOFF_TEMPLATE = """# Human Review Sign-off — `{name}` module

This is the mandatory human gate. The AI-generated evidence package under \
this product's `requirements/`, `design/`, `src/`, `tests/`, and `evidence/` \
directories is **draft** until this file is filled in and committed by a \
human reviewer.

## Reviewer

- **Name:**
- **Role:**
- **Date:**

## Checklist

- [ ] Requirements (`requirements/SRS.md`) reviewed and reflect the intended need
- [ ] Design (`design/SDD.md`) reviewed and traces cleanly to requirements
- [ ] Code (`src/{name}.py`) reviewed line-by-line, not just via test results
- [ ] Test suite (`tests/test_{name}.py`, `evidence/test-report.md`) reviewed \
- coverage and cases judged adequate, not just "all green"
- [ ] Static analysis results (`evidence/static-analysis-report.md`) reviewed
- [ ] Risk table (`evidence/risk-table.md`) reviewed, including any open items
- [ ] Traceability matrix (`evidence/traceability-matrix.md`) spot-checked \
against the source files, not taken on faith

## Decision

- [ ] **Approved** — evidence package accepted as-is
- [ ] **Approved with changes** — see notes
- [ ] **Rejected** — see notes

## Notes

_(free text)_
"""


def _strip_fences(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines)
    return text.strip() + "\n"


class Pipeline:
    """Runs one ProductSpec through all 8 stages."""

    def __init__(self, spec: ProductSpec):
        self.spec = spec
        self.client = LLMClient(model=spec.model)
        self.stage_log: dict[str, dict] = {}

    def run(self) -> None:
        self._scaffold()
        srs = self._run_requirements()
        sdd = self._run_design(srs)
        code = self._run_code(sdd)
        self._run_static_analysis()
        self._run_tests(srs, code)
        self._run_risk(srs, sdd)
        self._write_signoff_template()
        self._compile_evidence()

    def _scaffold(self) -> None:
        for sub in ("requirements", "design", "src", "tests", "evidence"):
            (self.spec.output_dir / sub).mkdir(parents=True, exist_ok=True)
        init_file = self.spec.output_dir / "src" / "__init__.py"
        if not init_file.exists():
            init_file.write_text("")
        conftest = self.spec.output_dir / "conftest.py"
        if not conftest.exists():
            conftest.write_text("")

    def _run_requirements(self) -> str:
        system, user = roles.requirements_prompt(self.spec)
        text = _strip_fences(self.client.complete(system, user))
        (self.spec.output_dir / "requirements" / "SRS.md").write_text(text)
        self.stage_log["requirements"] = {
            "agent_role": "Requirements Agent",
            "output": "requirements/SRS.md",
        }
        return text

    def _run_design(self, srs: str) -> str:
        system, user = roles.design_prompt(self.spec, srs)
        text = _strip_fences(self.client.complete(system, user))
        (self.spec.output_dir / "design" / "SDD.md").write_text(text)
        self.stage_log["design"] = {
            "agent_role": "Design Agent",
            "output": "design/SDD.md",
        }
        return text

    def _run_code(self, sdd: str) -> str:
        system, user = roles.code_prompt(self.spec, sdd)
        code = _strip_fences(self.client.complete(system, user))
        (self.spec.output_dir / "src" / f"{self.spec.name}.py").write_text(code)
        self.stage_log["code_generation"] = {
            "agent_role": "Code Generation Agent",
            "output": f"src/{self.spec.name}.py",
        }
        return code

    def _run_static_analysis(self) -> None:
        lint = tools.run_lint(self.spec.output_dir, self.spec.name)
        typecheck = tools.run_typecheck(self.spec.output_dir, self.spec.name)
        report = "\n".join(
            [
                f"# Static Analysis Report — `{self.spec.name}` module\n",
                "## ruff (lint)\n",
                f"Command: `{lint.command}`\n",
                "```",
                lint.combined_output or "(no output)",
                "```\n",
                "## mypy (type check, strict)\n",
                f"Command: `{typecheck.command}`\n",
                "```",
                typecheck.combined_output or "(no output)",
                "```\n",
            ]
        )
        (self.spec.output_dir / "evidence" / "static-analysis-report.md").write_text(report)
        self.stage_log["static_analysis"] = {
            "agent_role": "Static Analysis Agent",
            "output": "evidence/static-analysis-report.md",
            "verification": "real subprocess execution: ruff check, mypy --strict",
            "result": f"lint_ok={lint.ok}, typecheck_ok={typecheck.ok}",
        }

    def _run_tests(self, srs: str, code: str) -> None:
        system, user = roles.test_prompt(self.spec, srs, code)
        test_code = _strip_fences(self.client.complete(system, user))
        (self.spec.output_dir / "tests" / f"test_{self.spec.name}.py").write_text(test_code)

        result = tools.run_tests(self.spec.output_dir, self.spec.name)
        report = "\n".join(
            [
                f"# Test Execution Report — `{self.spec.name}` module\n",
                f"Command: `{result.command}`\n",
                f"Exit code: {result.exit_code}\n",
                "```",
                result.combined_output or "(no output)",
                "```\n",
            ]
        )
        (self.spec.output_dir / "evidence" / "test-report.md").write_text(report)
        self.stage_log["testing"] = {
            "agent_role": "Test Agent",
            "output": "evidence/test-report.md",
            "verification": "real subprocess execution: pytest + pytest-cov",
            "result": f"exit_code={result.exit_code}",
        }

    def _run_risk(self, srs: str, sdd: str) -> None:
        system, user = roles.risk_prompt(self.spec, srs, sdd)
        text = _strip_fences(self.client.complete(system, user))
        (self.spec.output_dir / "evidence" / "risk-table.md").write_text(text)
        self.stage_log["risk_analysis"] = {
            "agent_role": "Risk Analysis Agent",
            "output": "evidence/risk-table.md",
        }

    def _compile_evidence(self) -> None:
        matrix = evidence.build_traceability_matrix(self.spec.output_dir, self.spec.name)
        (self.spec.output_dir / "evidence" / "traceability-matrix.md").write_text(matrix)
        self.stage_log["evidence_compilation"] = {
            "agent_role": "Evidence Compiler",
            "output": "evidence/traceability-matrix.md",
            "verification": "regex-scanned REQ-* IDs across artifacts, not LLM-asserted",
        }
        evidence.write_provenance(
            self.spec.output_dir,
            self.spec.name,
            self.spec.safety_class,
            self.spec.model,
            self.stage_log,
        )

    def _write_signoff_template(self) -> None:
        path = self.spec.output_dir / "evidence" / "review-signoff.md"
        if not path.exists():
            path.write_text(SIGNOFF_TEMPLATE.format(name=self.spec.name))
        self.stage_log["human_gate"] = {
            "agent_role": "Human Gate",
            "output": "evidence/review-signoff.md",
            "verification": "pending - requires human signature, not auto-completed",
        }
