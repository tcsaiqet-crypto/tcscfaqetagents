"""Unit tests for Phase 3 Test Case Generation Agent & Artifacts."""

import csv
import json
import pytest
from pathlib import Path
from schemas.contracts import AppState
from src.agents.test_case_agent import TestCaseAgent


def test_generate_all_5_test_case_types(tmp_path: Path) -> None:
    agent = TestCaseAgent(run_id="RUN-TEST-TC1")
    agent.artifact_dir = tmp_path
    
    state = AppState(run_id="RUN-TEST-TC1")
    updated = agent.run(state)
    
    suite = updated.test_suite
    assert suite is not None
    assert len(suite.test_cases) >= 10
    
    types_found = {tc.case_type for tc in suite.test_cases}
    expected_types = {"Positive", "Negative", "Boundary", "Validation", "Error-Handling"}
    assert expected_types.issubset(types_found), f"Missing test case types: {expected_types - types_found}"


def test_test_case_contract_fields(tmp_path: Path) -> None:
    agent = TestCaseAgent(run_id="RUN-TEST-TC2")
    cases = agent._generate_test_cases()
    
    for tc in cases:
        assert tc.case_id != ""
        assert tc.title != ""
        assert tc.case_type in ["Positive", "Negative", "Boundary", "Validation", "Error-Handling"]
        assert tc.priority in ["Critical", "High", "Medium", "Low"]
        assert tc.risk_level in ["High", "Medium", "Low"]
        assert tc.review_status in ["Generated", "Requires Review", "Approved", "Needs Revision"]
        assert isinstance(tc.automation_candidate, bool)
        assert len(tc.steps) > 0
        assert tc.expected_result != ""


def test_artifact_generation_json_csv_matrix(tmp_path: Path) -> None:
    run_id = "RUN-TEST-TC3"
    agent = TestCaseAgent(run_id=run_id)
    agent.artifact_dir = tmp_path
    
    state = AppState(run_id=run_id)
    agent.run(state)
    
    json_path = tmp_path / "test_cases.json"
    csv_path = tmp_path / "test_cases.csv"
    matrix_path = tmp_path / "traceability_matrix.json"
    
    assert json_path.exists()
    assert csv_path.exists()
    assert matrix_path.exists()
    
    # Validate JSON artifact
    json_data = json.loads(json_path.read_text(encoding="utf-8"))
    assert isinstance(json_data, list)
    assert len(json_data) >= 10
    
    # Validate Traceability Matrix artifact
    matrix_data = json.loads(matrix_path.read_text(encoding="utf-8"))
    assert "requirement_to_tests" in matrix_data
    assert "component_to_tests" in matrix_data


def test_csv_export_format(tmp_path: Path) -> None:
    agent = TestCaseAgent(run_id="RUN-TEST-TC4")
    agent.artifact_dir = tmp_path
    
    state = AppState(run_id="RUN-TEST-TC4")
    agent.run(state)
    
    csv_path = tmp_path / "test_cases.csv"
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        assert len(rows) >= 10
        first_row = rows[0]
        assert "case_id" in first_row
        assert "title" in first_row
        assert "case_type" in first_row
        assert "priority" in first_row
        assert "review_status" in first_row
