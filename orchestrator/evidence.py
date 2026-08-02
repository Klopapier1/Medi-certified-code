"""Traceability compilation and provenance recording.

Mechanical, regex-based cross-referencing of REQ-*/D-* IDs across a
product's artifacts. Deliberately not LLM-generated: the whole point of the
traceability matrix is that it's verified against the actual files, not
asserted by the same kind of model that wrote them.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

REQ_PATTERN = re.compile(r"REQ-\d+")
DESIGN_PATTERN = re.compile(r"D-\d+")


def extract_ids(text: str, pattern: re.Pattern[str]) -> set[str]:
    return set(pattern.findall(text))


def _ids_in_file(path: Path, pattern: re.Pattern[str]) -> set[str]:
    if not path.exists():
        return set()
    return extract_ids(path.read_text(), pattern)


@dataclass(frozen=True)
class ProductPaths:
    root: Path
    module_name: str

    @property
    def srs(self) -> Path:
        return self.root / "requirements" / "SRS.md"

    @property
    def sdd(self) -> Path:
        return self.root / "design" / "SDD.md"

    @property
    def code(self) -> Path:
        return self.root / "src" / f"{self.module_name}.py"

    @property
    def tests(self) -> Path:
        return self.root / "tests" / f"test_{self.module_name}.py"

    @property
    def risk_table(self) -> Path:
        return self.root / "evidence" / "risk-table.md"


def build_traceability_matrix(product_dir: Path, module_name: str) -> str:
    paths = ProductPaths(product_dir, module_name)

    req_ids_by_stage = {
        "srs": _ids_in_file(paths.srs, REQ_PATTERN),
        "sdd": _ids_in_file(paths.sdd, REQ_PATTERN),
        "code": _ids_in_file(paths.code, REQ_PATTERN),
        "tests": _ids_in_file(paths.tests, REQ_PATTERN),
        "risk": _ids_in_file(paths.risk_table, REQ_PATTERN),
    }
    all_reqs = sorted(req_ids_by_stage["srs"], key=lambda r: int(r.split("-")[1]))

    orphans = {
        stage: sorted(ids - req_ids_by_stage["srs"], key=lambda r: int(r.split("-")[1]))
        for stage, ids in req_ids_by_stage.items()
        if stage != "srs" and (ids - req_ids_by_stage["srs"])
    }

    lines = [
        f"# Traceability Matrix — `{module_name}` module\n",
        "Auto-compiled by `orchestrator/evidence.py` by scanning REQ-* IDs "
        "present in each artifact file. Not asserted by the generating agent.\n",
        "| Requirement | In SDD | In code | In tests | In risk table |",
        "|---|---|---|---|---|",
    ]
    for req in all_reqs:
        lines.append(
            f"| {req} "
            f"| {'yes' if req in req_ids_by_stage['sdd'] else '**MISSING**'} "
            f"| {'yes' if req in req_ids_by_stage['code'] else '**MISSING**'} "
            f"| {'yes' if req in req_ids_by_stage['tests'] else '**MISSING**'} "
            f"| {'yes' if req in req_ids_by_stage['risk'] else 'not referenced'} |"
        )

    lines.append("\n## Coverage check\n")
    if not all_reqs:
        lines.append("- No REQ-* IDs found in `requirements/SRS.md`.")
    else:
        missing_anywhere = [
            req
            for req in all_reqs
            if req not in req_ids_by_stage["sdd"]
            or req not in req_ids_by_stage["code"]
            or req not in req_ids_by_stage["tests"]
        ]
        if missing_anywhere:
            lines.append(
                "- **Gap:** requirement(s) missing from at least one "
                f"downstream artifact: {', '.join(missing_anywhere)}"
            )
        else:
            lines.append(
                "- Every requirement in SRS.md has a matching design "
                "reference, code reference, and test reference."
            )

    for stage, ids in orphans.items():
        lines.append(
            f"- **Gap:** {stage} references ID(s) not present in SRS.md: "
            f"{', '.join(ids)}"
        )

    return "\n".join(lines) + "\n"


def write_provenance(
    product_dir: Path,
    module_name: str,
    safety_class: str,
    model: str,
    stage_log: dict,
) -> None:
    provenance = {
        "pipelineRun": {
            "date": datetime.now(timezone.utc).date().isoformat(),
            "mode": "automated-orchestrator",
            "item": f"{module_name} module (IEC 62304 Class {safety_class})",
            "model": model,
        },
        "stages": stage_log,
        "limitations": [
            "No claim of regulatory certification or submission-readiness "
            "is made by this provenance record.",
            "The traceability matrix checks ID presence/cross-referencing "
            "only; it does not verify that a requirement's test is actually "
            "a meaningful test of that requirement's behavior — that's the "
            "human reviewer's job (see evidence/review-signoff.md).",
        ],
    }
    (product_dir / "evidence" / "run-provenance.json").write_text(
        json.dumps(provenance, indent=2) + "\n"
    )
