from pathlib import Path

from orchestrator import evidence

BMI_PRODUCT = Path(__file__).resolve().parents[2] / "products" / "bmi"


def test_extract_ids_dedupes():
    ids = evidence.extract_ids("REQ-001 and REQ-002, then REQ-001 again", evidence.REQ_PATTERN)
    assert ids == {"REQ-001", "REQ-002"}


def test_extract_ids_empty_when_no_match():
    assert evidence.extract_ids("nothing here", evidence.REQ_PATTERN) == set()


def test_traceability_matrix_lists_all_bmi_requirements():
    matrix = evidence.build_traceability_matrix(BMI_PRODUCT, "bmi")
    for req in ("REQ-001", "REQ-002", "REQ-003", "REQ-004"):
        assert req in matrix


def test_traceability_matrix_no_gaps_for_bmi_pilot():
    # The BMI pilot's hand-authored artifacts were built to fully trace;
    # this proves the mechanical scan agrees with that by-hand claim.
    matrix = evidence.build_traceability_matrix(BMI_PRODUCT, "bmi")
    assert "MISSING" not in matrix
    assert "Gap" not in matrix


def test_traceability_matrix_flags_a_missing_requirement(tmp_path):
    product = tmp_path / "product"
    (product / "requirements").mkdir(parents=True)
    (product / "design").mkdir()
    (product / "src").mkdir()
    (product / "tests").mkdir()
    (product / "evidence").mkdir()

    (product / "requirements" / "SRS.md").write_text(
        "### REQ-001 — thing\n### REQ-002 — other\n", encoding="utf-8"
    )
    (product / "design" / "SDD.md").write_text(
        "D-01 traces to REQ-001\n", encoding="utf-8"
    )  # REQ-002 missing
    (product / "src" / "widget.py").write_text("# REQ-001\n# REQ-002\n", encoding="utf-8")
    (product / "tests" / "test_widget.py").write_text(
        "# REQ-001\n", encoding="utf-8"
    )  # REQ-002 missing

    matrix = evidence.build_traceability_matrix(product, "widget")
    assert "**Gap:**" in matrix
    assert "REQ-002" in matrix


def test_write_provenance_creates_valid_json(tmp_path):
    product = tmp_path / "product"
    (product / "evidence").mkdir(parents=True)

    evidence.write_provenance(
        product,
        module_name="widget",
        safety_class="A",
        model="claude-sonnet-5",
        stage_log={"requirements": {"agent_role": "Requirements Agent"}},
    )

    import json

    data = json.loads((product / "evidence" / "run-provenance.json").read_text())
    assert data["pipelineRun"]["item"] == "widget module (IEC 62304 Class A)"
    assert "requirements" in data["stages"]
