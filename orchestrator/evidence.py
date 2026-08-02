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
from typing import Any

REQ_PATTERN = re.compile(r"REQ-\d+")
DESIGN_PATTERN = re.compile(r"D-\d+")
RISK_PATTERN = re.compile(r"RISK-\d+")


def extract_ids(text: str, pattern: re.Pattern[str]) -> set[str]:
    return set(pattern.findall(text))


def _ids_in_file(path: Path, pattern: re.Pattern[str]) -> set[str]:
    if not path.exists():
        return set()
    return extract_ids(path.read_text(encoding="utf-8"), pattern)


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
    """Renders the traceability matrix by building the Certification Knowledge
    Graph (orchestrator/ckg.py) and projecting it to Markdown. Kept in this
    module (rather than moved wholesale to ckg.py) since it's the pipeline's
    long-standing public entry point; the implementation now lives in
    ckg.render_traceability_matrix, sourced from graph.coverage — a whole-file
    REQ-* scan per stage using the exact same primitives as before
    (_ids_in_file/REQ_PATTERN), so output is unchanged.

    Imported lazily to avoid a circular import: ckg.py imports the ID-pattern
    primitives from this module at load time.
    """
    from . import ckg as ckg_module

    graph = ckg_module.build_graph(product_dir, module_name)
    return ckg_module.render_traceability_matrix(graph, module_name)


def write_provenance(
    product_dir: Path,
    module_name: str,
    safety_class: str,
    model: str,
    stage_log: dict[str, Any],
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
        json.dumps(provenance, indent=2) + "\n", encoding="utf-8"
    )
