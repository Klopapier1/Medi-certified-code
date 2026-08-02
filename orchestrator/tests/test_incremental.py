from orchestrator import ckg, incremental


def _graph_with(*nodes: tuple[str, str]) -> ckg.CKG:
    graph = ckg.CKG()
    for node_id, node_type in nodes:
        graph.add_node(ckg.Node(node_id, node_type))
    return graph


def test_requirement_change_triggers_full_rerun() -> None:
    graph = _graph_with(("REQ-001", "Requirement"))
    assert incremental.impacted_stages(graph, ["REQ-001"]) == list(
        incremental.STAGE_ORDER
    )


def test_design_element_change_skips_requirements_and_design() -> None:
    graph = _graph_with(("D-01", "DesignElement"))
    stages = incremental.impacted_stages(graph, ["D-01"])
    assert "requirements" not in stages
    assert "design" not in stages
    assert stages == ["code_generation", "static_analysis", "testing", "evidence_compilation"]


def test_test_case_change_only_recompiles_evidence() -> None:
    graph = _graph_with(("test:TestREQ001Thing", "TestCase"))
    assert incremental.impacted_stages(graph, ["test:TestREQ001Thing"]) == [
        "evidence_compilation"
    ]


def test_risk_row_change_only_recompiles_evidence() -> None:
    graph = _graph_with(("RISK-001", "RiskRow"))
    assert incremental.impacted_stages(graph, ["RISK-001"]) == ["evidence_compilation"]


def test_unknown_node_id_falls_back_to_evidence_compilation_only() -> None:
    graph = ckg.CKG()
    assert incremental.impacted_stages(graph, ["REQ-999"]) == ["evidence_compilation"]


def test_multiple_changed_nodes_union_their_stages() -> None:
    graph = _graph_with(("D-01", "DesignElement"), ("RISK-001", "RiskRow"))
    stages = incremental.impacted_stages(graph, ["D-01", "RISK-001"])
    # union of DesignElement's stages and RiskRow's (subset), still ordered
    assert stages == ["code_generation", "static_analysis", "testing", "evidence_compilation"]


def test_stage_order_is_always_respected_regardless_of_input_order() -> None:
    graph = _graph_with(("REQ-001", "Requirement"), ("D-01", "DesignElement"))
    stages = incremental.impacted_stages(graph, ["D-01", "REQ-001"])
    assert stages == list(incremental.STAGE_ORDER)
