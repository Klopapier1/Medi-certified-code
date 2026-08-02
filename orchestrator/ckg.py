"""Certification Knowledge Graph: structured traceability over product artifacts.

Phase 2 (Living Traceability). Parses the same artifact files
`evidence.py` has always scanned (SRS.md, SDD.md, source, tests,
risk-table.md) into an explicit node/edge graph instead of a flat
regex-diffed presence table.

Two things are deliberately kept separate:

- `CKG.coverage`: a whole-file REQ-* presence scan per artifact stage,
  computed with the exact same primitives `evidence.py` always used
  (`_ids_in_file`/`REQ_PATTERN`). This is the sole input to
  `render_traceability_matrix`, so the traceability matrix stays
  byte-identical to the pre-graph implementation.
- `CKG.nodes` / `CKG.edges`: structured entities (one node per
  requirement, design element, test class, risk row, ...) parsed from
  table rows / class definitions. This is what change-impact analysis,
  the graph explorer, and incremental regeneration query — it is a
  strict superset of what the flat matrix needed, not a replacement
  for the coverage scan.

The public `CKG` surface (attributed nodes/edges, `edges_to`/
`edges_from` traversal) is deliberately shaped like `networkx.DiGraph`
so that if a future phase needs real graph algorithms, swapping the
internal representation is mechanical rather than a rewrite of every
call site. No graph library is used here — Phase 2's graphs are a few
dozen nodes per product, so a dependency isn't justified yet.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .evidence import (
    DESIGN_PATTERN,
    REQ_PATTERN,
    RISK_PATTERN,
    ProductPaths,
    _ids_in_file,
)

SCHEMA_VERSION = 1

_TABLE_ROW_SEPARATOR = re.compile(r"^[\s|:-]+$")


@dataclass
class Node:
    id: str
    type: str
    label: str = ""


@dataclass(frozen=True)
class Edge:
    source: str
    target: str
    type: str


@dataclass
class CKG:
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    coverage: dict[str, set[str]] = field(default_factory=dict)

    def add_node(self, node: Node) -> None:
        if node.id not in self.nodes:
            self.nodes[node.id] = node

    def add_edge(self, source: str, target: str, edge_type: str) -> None:
        edge = Edge(source, target, edge_type)
        if edge not in self.edges:
            self.edges.append(edge)

    def get_node(self, node_id: str) -> Node | None:
        return self.nodes.get(node_id)

    def edges_to(self, node_id: str) -> list[Edge]:
        return [e for e in self.edges if e.target == node_id]

    def edges_from(self, node_id: str) -> list[Edge]:
        return [e for e in self.edges if e.source == node_id]

    def downstream_impact(self, node_ids: str | Iterable[str]) -> set[str]:
        """IDs of nodes that transitively point at `node_ids` (i.e. would be
        affected if `node_ids` changed). Edges are authored dependent -> depended-on
        (e.g. `DesignElement -IMPLEMENTS-> Requirement`), so impact walks
        edges_to() — incoming edges — not edges_from()."""
        start = {node_ids} if isinstance(node_ids, str) else set(node_ids)
        impacted: set[str] = set()
        frontier = start
        while frontier:
            next_frontier: set[str] = set()
            for nid in frontier:
                for e in self.edges_to(nid):
                    if e.source not in impacted and e.source not in start:
                        impacted.add(e.source)
                        next_frontier.add(e.source)
            frontier = next_frontier
        return impacted

    def to_dict(self) -> dict[str, Any]:
        return {
            "schemaVersion": SCHEMA_VERSION,
            "nodes": [
                {"id": n.id, "type": n.type, "label": n.label}
                for n in self.nodes.values()
            ],
            "edges": [
                {"source": e.source, "target": e.target, "type": e.type}
                for e in self.edges
            ],
            "coverage": {stage: sorted(ids) for stage, ids in self.coverage.items()},
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CKG":
        graph = cls()
        for n in data.get("nodes", []):
            graph.add_node(Node(id=n["id"], type=n["type"], label=n.get("label", "")))
        for e in data.get("edges", []):
            graph.add_edge(e["source"], e["target"], e["type"])
        graph.coverage = {
            stage: set(ids) for stage, ids in data.get("coverage", {}).items()
        }
        return graph


def _is_table_row(line: str) -> str | None:
    """Return the stripped line if it's a Markdown table content row
    (starts with '|', not a header separator like '|---|---|'), else None."""
    stripped = line.strip()
    if not stripped.startswith("|"):
        return None
    if _TABLE_ROW_SEPARATOR.match(stripped):
        return None
    return stripped


def _parse_requirements(graph: CKG, srs_text: str) -> None:
    heading = re.compile(r"^### (REQ-\d+) — (.+)$")
    for line in srs_text.splitlines():
        m = heading.match(line.strip())
        if m:
            graph.add_node(Node(id=m.group(1), type="Requirement", label=m.group(2)))


def _table_cells(row: str) -> list[str]:
    return [c.strip() for c in row.strip("|").split("|")]


def _parse_design_elements(graph: CKG, sdd_text: str) -> None:
    # Only the first cell (ID column) and last cell (REQ-refs column) are
    # scanned for IDs - a description cell can mention *other* D-IDs as
    # prose (e.g. "covered by D-02's lower bounds"), which must not be
    # read as that row's own design element implementing this row's REQ.
    for line in sdd_text.splitlines():
        row = _is_table_row(line)
        if row is None:
            continue
        cells = _table_cells(row)
        if len(cells) < 2:
            continue
        design_ids = DESIGN_PATTERN.findall(cells[0])
        req_ids = REQ_PATTERN.findall(cells[-1])
        if not design_ids or not req_ids:
            continue
        for d in design_ids:
            graph.add_node(Node(id=d, type="DesignElement"))
            for r in req_ids:
                graph.add_edge(d, r, "IMPLEMENTS")


def _parse_code_artifact(graph: CKG, module_name: str) -> None:
    code_id = f"code:{module_name}"
    graph.add_node(Node(id=code_id, type="CodeArtifact", label=f"src/{module_name}.py"))
    for r in graph.coverage.get("code", set()):
        graph.add_edge(code_id, r, "IMPLEMENTS")


def _parse_test_cases(graph: CKG, tests_text: str) -> None:
    # Stored as TestCase -> Requirement (dependent -> depended-upon), the same
    # direction convention as IMPLEMENTS/MITIGATES, so downstream_impact's
    # single "walk incoming edges" rule works uniformly across all edge types
    # (a test verifying REQ-002 is impacted if REQ-002 changes). Render as
    # "Requirement verified by TestCase" wherever the natural reading matters.
    class_pattern = re.compile(r"^class (Test(?:REQ)(\d+)\w*)\b")
    for line in tests_text.splitlines():
        m = class_pattern.match(line.strip())
        if m:
            class_name, digits = m.group(1), m.group(2)
            req_id = f"REQ-{digits}"
            test_id = f"test:{class_name}"
            graph.add_node(Node(id=test_id, type="TestCase", label=class_name))
            graph.add_edge(test_id, req_id, "VERIFIED_BY")


def _parse_risk_rows(graph: CKG, risk_text: str) -> None:
    # Only the ID column and the (header-detected) Mitigation column are
    # scanned for edge targets - other columns (Hazard, Possible cause,
    # Potential effect, Residual risk) can plausibly mention IDs in prose
    # without that row actually mitigating them.
    rows = [r for r in (_is_table_row(line) for line in risk_text.splitlines()) if r is not None]
    if not rows:
        return

    header_cells = [c.lower() for c in _table_cells(rows[0])]
    mitigation_col = header_cells.index("mitigation") if "mitigation" in header_cells else None

    for row in rows[1:]:
        cells = _table_cells(row)
        if not cells:
            continue
        risk_ids = RISK_PATTERN.findall(cells[0])
        if not risk_ids:
            continue
        target_text = (
            cells[mitigation_col]
            if mitigation_col is not None and mitigation_col < len(cells)
            else ""
        )
        req_ids = REQ_PATTERN.findall(target_text)
        design_ids = DESIGN_PATTERN.findall(target_text)
        for rid in risk_ids:
            graph.add_node(Node(id=rid, type="RiskRow"))
            for target in (*req_ids, *design_ids):
                graph.add_edge(rid, target, "MITIGATES")


_EVIDENCE_FILES = (
    "static-analysis-report.md",
    "test-report.md",
    "run-provenance.json",
    "sbom.json",
    "review-signoff.md",
)


def _parse_evidence_artifacts(graph: CKG, product_dir: Path) -> None:
    evidence_dir = product_dir / "evidence"
    for fname in _EVIDENCE_FILES:
        if (evidence_dir / fname).exists():
            graph.add_node(Node(id=f"evidence:{fname}", type="EvidenceArtifact", label=fname))


def build_graph(product_dir: Path, module_name: str) -> CKG:
    paths = ProductPaths(product_dir, module_name)
    graph = CKG()

    graph.coverage = {
        "srs": _ids_in_file(paths.srs, REQ_PATTERN),
        "sdd": _ids_in_file(paths.sdd, REQ_PATTERN),
        "code": _ids_in_file(paths.code, REQ_PATTERN),
        "tests": _ids_in_file(paths.tests, REQ_PATTERN),
        "risk": _ids_in_file(paths.risk_table, REQ_PATTERN),
    }

    if paths.srs.exists():
        _parse_requirements(graph, paths.srs.read_text(encoding="utf-8"))
    if paths.sdd.exists():
        _parse_design_elements(graph, paths.sdd.read_text(encoding="utf-8"))
    if paths.code.exists():
        _parse_code_artifact(graph, module_name)
    if paths.tests.exists():
        _parse_test_cases(graph, paths.tests.read_text(encoding="utf-8"))
    if paths.risk_table.exists():
        _parse_risk_rows(graph, paths.risk_table.read_text(encoding="utf-8"))
    _parse_evidence_artifacts(graph, product_dir)

    return graph


def write_graph(product_dir: Path, module_name: str) -> CKG:
    graph = build_graph(product_dir, module_name)
    (product_dir / "evidence" / "ckg.json").write_text(
        json.dumps(graph.to_dict(), indent=2) + "\n", encoding="utf-8"
    )
    return graph


def render_traceability_matrix(graph: CKG, module_name: str) -> str:
    """Renders the same Markdown traceability matrix `evidence.py` has
    always produced, sourced from `graph.coverage` (a whole-file REQ-*
    scan per stage, identical to the pre-graph implementation) rather
    than a fresh regex pass over the files."""
    req_ids_by_stage = graph.coverage
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
