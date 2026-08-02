"""Incremental regeneration: re-run only the pipeline stages downstream of a
set of changed CKG nodes, instead of the full 8-stage Pipeline.run().

`impacted_stages()` is a pure function (graph + changed IDs -> ordered stage
list, no I/O, no LLM calls) so the stage-selection logic is unit-testable on
its own. `regenerate_from()` is the thin glue that loads the persisted graph
and drives Pipeline's stage methods in dependency order.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from . import ckg
from .config import ProductSpec
from .pipeline import Pipeline

# Mirrors Pipeline.run()'s stage sequence (excluding scaffold/human_gate,
# which are idempotent/independent of what changed).
STAGE_ORDER = (
    "requirements",
    "design",
    "code_generation",
    "static_analysis",
    "testing",
    "risk_analysis",
    "evidence_compilation",
)

# Which stages must rerun if a node of this type changed. A node's stage
# never includes stages upstream of where that node type is produced/consumed
# - e.g. a DesignElement change never re-triggers "requirements". Everything
# always includes evidence_compilation (cheap, idempotent, keeps the
# traceability matrix / ckg.json in sync regardless of what else ran).
_TYPE_TO_STAGES: dict[str, frozenset[str]] = {
    "Requirement": frozenset(STAGE_ORDER),
    "DesignElement": frozenset(
        {"code_generation", "static_analysis", "testing", "evidence_compilation"}
    ),
    "CodeArtifact": frozenset({"static_analysis", "testing", "evidence_compilation"}),
    "TestCase": frozenset({"evidence_compilation"}),
    "RiskRow": frozenset({"evidence_compilation"}),
    "EvidenceArtifact": frozenset({"evidence_compilation"}),
}


def impacted_stages(graph: ckg.CKG, changed_node_ids: Iterable[str]) -> list[str]:
    """Ordered list of pipeline stages to rerun for the given changed node
    IDs. Unknown node IDs conservatively trigger evidence_compilation only."""
    stages: set[str] = {"evidence_compilation"}
    for node_id in changed_node_ids:
        node = graph.get_node(node_id)
        stages |= (
            _TYPE_TO_STAGES.get(node.type, {"evidence_compilation"})
            if node is not None
            else {"evidence_compilation"}
        )
    return [s for s in STAGE_ORDER if s in stages]


def _read_if_exists(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def regenerate_from(spec: ProductSpec, changed_node_ids: Iterable[str]) -> list[str]:
    """Regenerate only the artifacts downstream of `changed_node_ids`. Falls
    back to a full Pipeline.run() if no evidence/ckg.json snapshot exists yet
    (nothing to diff against). Returns the list of stages actually executed.

    Calls Pipeline's underscore-prefixed _run_* methods directly - they
    already take upstream text as explicit parameters (_run_design(srs),
    _run_code(sdd), _run_tests(srs, code)), so the dependency chain is
    expressed in their signatures rather than duplicated here.
    """
    graph_path = spec.output_dir / "evidence" / "ckg.json"
    if not graph_path.exists():
        Pipeline(spec).run()
        return list(STAGE_ORDER)

    graph = ckg.CKG.from_dict(json.loads(graph_path.read_text(encoding="utf-8")))
    stages = impacted_stages(graph, changed_node_ids)

    pipeline = Pipeline(spec)
    srs = _read_if_exists(spec.output_dir / "requirements" / "SRS.md")
    sdd = _read_if_exists(spec.output_dir / "design" / "SDD.md")
    code = _read_if_exists(spec.output_dir / "src" / f"{spec.name}.py")

    if "requirements" in stages:
        srs = pipeline._run_requirements()
    if "design" in stages:
        sdd = pipeline._run_design(srs)
    if "code_generation" in stages:
        code = pipeline._run_code(sdd)
    if "static_analysis" in stages:
        pipeline._run_static_analysis()
    if "testing" in stages:
        pipeline._run_tests(srs, code)
    if "risk_analysis" in stages:
        pipeline._run_risk(srs, sdd)
    pipeline._compile_evidence()

    return stages
