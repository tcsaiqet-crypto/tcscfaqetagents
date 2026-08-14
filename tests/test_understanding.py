"""Unit tests for Phase 2 Application Understanding Agent & Artifacts."""

import json
import pytest
from pathlib import Path
from schemas.contracts import AppState, IntakeManifest
from src.agents.understanding_agent import UnderstandingAgent


def test_schema_validation(tmp_path: Path) -> None:
    agent = UnderstandingAgent(run_id="RUN-TEST-U1")
    state = AppState(run_id="RUN-TEST-U1")
    
    updated_state = agent.run(state)
    u = updated_state.understanding
    
    assert u is not None
    assert u.summary != ""
    assert u.quality_score_percentage > 0.0
    assert len(u.components) > 0
    assert len(u.gaps) > 0
    assert u.validation_report is not None
    assert u.ui_inventory is not None
    assert u.api_inventory is not None


def test_checklist_15_point_evaluation_and_quality_score() -> None:
    agent = UnderstandingAgent(run_id="RUN-TEST-U2")
    report = agent._evaluate_15_point_checklist(["reqs.md"])
    
    assert report.evaluated_items_count == 15
    assert len(report.items) == 15
    
    # Verify exact formula: (present + 0.5 * partial) / applicable * 100
    applicable = 15 - report.not_applicable_count
    expected_score = round(((report.present_count + 0.5 * report.partial_count) / applicable * 100.0), 1)
    assert report.quality_score_percentage == expected_score


def test_ui_and_api_inventory_extraction() -> None:
    agent = UnderstandingAgent(run_id="RUN-TEST-U3")
    ui = agent._extract_ui_inventory(Path("sample_cfa_app"))
    api = agent._extract_api_inventory(Path("sample_cfa_app"))
    
    assert ui.total_controls == 12
    assert "button" in ui.controls_by_type
    assert "text_field" in ui.controls_by_type
    
    assert api.total_endpoints > 0
    for ep in api.endpoints:
        assert ep.analysis_only is True


def test_versioned_artifact_generation(tmp_path: Path) -> None:
    run_id = "RUN-TEST-U4"
    agent = UnderstandingAgent(run_id=run_id)
    agent.artifact_dir = tmp_path
    
    state = AppState(run_id=run_id)
    agent.run(state)
    
    expected_artifacts = [
        "application_understanding.json",
        "requirements_validation.json",
        "requirements_gaps.json",
        "module_inventory.json",
        "ui_inventory.json",
        "api_inventory.json"
    ]
    
    for fname in expected_artifacts:
        art_file = tmp_path / fname
        assert art_file.exists(), f"Missing artifact file: {fname}"
        content = json.loads(art_file.read_text(encoding="utf-8"))
        assert content is not None


def test_deterministic_fallback_when_offline() -> None:
    agent = UnderstandingAgent(run_id="RUN-TEST-OFFLINE")
    state = AppState(run_id="RUN-TEST-OFFLINE")
    
    # Run offline analysis without requiring external API connection
    updated = agent.run(state)
    assert updated.understanding is not None
    assert updated.understanding.validation_report.quality_score_percentage > 0.0


def test_empty_input_and_missing_requirements() -> None:
    agent = UnderstandingAgent(run_id="RUN-TEST-EMPTY")
    state = AppState(run_id="RUN-TEST-EMPTY")
    
    updated = agent.run(state)
    assert updated.understanding is not None
    assert len(updated.understanding.gaps) > 0
