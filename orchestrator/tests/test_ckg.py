from pathlib import Path

from orchestrator import ckg

BMI_PRODUCT = Path(__file__).resolve().parents[2] / "products" / "bmi"


def _bmi_graph() -> ckg.CKG:
    return ckg.build_graph(BMI_PRODUCT, "bmi")


def test_bmi_graph_node_counts_by_type() -> None:
    graph = _bmi_graph()
    counts: dict[str, int] = {}
    for node in graph.nodes.values():
        counts[node.type] = counts.get(node.type, 0) + 1

    assert counts["Requirement"] == 4
    assert counts["DesignElement"] == 6
    assert counts["CodeArtifact"] == 1
    assert counts["TestCase"] == 4
    assert counts["RiskRow"] == 5
    assert counts["EvidenceArtifact"] == 5


def test_bmi_graph_implements_edges() -> None:
    graph = _bmi_graph()
    assert ckg.Edge("D-04", "REQ-001", "IMPLEMENTS") in graph.edges
    assert ckg.Edge("D-02", "REQ-004", "IMPLEMENTS") in graph.edges
    assert ckg.Edge("code:bmi", "REQ-001", "IMPLEMENTS") in graph.edges
    assert ckg.Edge("code:bmi", "REQ-004", "IMPLEMENTS") in graph.edges


def test_bmi_graph_verified_by_edges_point_test_to_requirement() -> None:
    graph = _bmi_graph()
    assert (
        ckg.Edge("test:TestREQ002InputValidation", "REQ-002", "VERIFIED_BY")
        in graph.edges
    )


def test_bmi_graph_mitigates_edges_can_target_a_design_element() -> None:
    # RISK-004's mitigation cites "D-01 in SDD" only, no REQ-* on that row.
    graph = _bmi_graph()
    assert ckg.Edge("RISK-004", "D-01", "MITIGATES") in graph.edges


def test_bmi_graph_deduplicates_design_edges_seen_in_two_tables() -> None:
    # D-01 and D-03 each appear once in the functional table and once in the
    # "Traceability summary" table with the same REQ-002 target; edges must
    # not be double-counted. code:bmi also implements REQ-002 (whole-file
    # scan), so it's a legitimate third source here.
    graph = _bmi_graph()
    implements_to_req002 = [
        e for e in graph.edges if e.type == "IMPLEMENTS" and e.target == "REQ-002"
    ]
    assert sorted(e.source for e in implements_to_req002) == ["D-01", "D-03", "code:bmi"]


def test_bmi_graph_coverage_matches_legacy_regex_scan() -> None:
    from orchestrator.evidence import REQ_PATTERN, _ids_in_file, ProductPaths

    graph = _bmi_graph()
    paths = ProductPaths(BMI_PRODUCT, "bmi")
    assert graph.coverage["sdd"] == _ids_in_file(paths.sdd, REQ_PATTERN)
    assert graph.coverage["code"] == _ids_in_file(paths.code, REQ_PATTERN)
    assert graph.coverage["tests"] == _ids_in_file(paths.tests, REQ_PATTERN)


def test_downstream_impact_on_synthetic_graph() -> None:
    graph = ckg.CKG()
    graph.add_node(ckg.Node("REQ-001", "Requirement"))
    graph.add_node(ckg.Node("D-01", "DesignElement"))
    graph.add_node(ckg.Node("code:widget", "CodeArtifact"))
    graph.add_node(ckg.Node("test:TestREQ001Thing", "TestCase"))
    graph.add_node(ckg.Node("RISK-001", "RiskRow"))
    graph.add_node(ckg.Node("REQ-002", "Requirement"))

    graph.add_edge("D-01", "REQ-001", "IMPLEMENTS")
    graph.add_edge("code:widget", "REQ-001", "IMPLEMENTS")
    graph.add_edge("test:TestREQ001Thing", "REQ-001", "VERIFIED_BY")
    graph.add_edge("RISK-001", "D-01", "MITIGATES")  # transitively depends on REQ-001

    impacted = graph.downstream_impact("REQ-001")

    assert impacted == {"D-01", "code:widget", "test:TestREQ001Thing", "RISK-001"}
    assert "REQ-002" not in impacted


def test_downstream_impact_accepts_multiple_seed_ids() -> None:
    graph = ckg.CKG()
    graph.add_edge("D-01", "REQ-001", "IMPLEMENTS")
    graph.add_edge("D-02", "REQ-002", "IMPLEMENTS")

    impacted = graph.downstream_impact(["REQ-001", "REQ-002"])

    assert impacted == {"D-01", "D-02"}


def test_downstream_impact_empty_for_unknown_node() -> None:
    graph = ckg.CKG()
    graph.add_edge("D-01", "REQ-001", "IMPLEMENTS")

    assert graph.downstream_impact("REQ-999") == set()


def test_to_dict_from_dict_round_trip() -> None:
    graph = _bmi_graph()
    restored = ckg.CKG.from_dict(graph.to_dict())

    assert set(restored.nodes) == set(graph.nodes)
    assert set(restored.edges) == set(graph.edges)
    assert restored.coverage == graph.coverage
