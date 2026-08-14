"""Unit tests for Phase 4 Synthetic Test Data Agent & Non-PII Compliance."""

import json
import pytest
from pathlib import Path
from schemas.contracts import AppState
from src.agents.test_data_agent import TestDataAgent


def test_synthetic_data_generation_and_schema(tmp_path: Path) -> None:
    agent = TestDataAgent(run_id="RUN-TEST-SD1")
    agent.artifact_dir = tmp_path
    
    state = AppState(run_id="RUN-TEST-SD1")
    updated = agent.run(state)
    
    dataset = updated.synthetic_dataset
    assert dataset is not None
    assert dataset.is_synthetic is True
    assert len(dataset.records) >= 5
    assert len(dataset.test_case_id_mapping) > 0


def test_non_pii_compliance(tmp_path: Path) -> None:
    agent = TestDataAgent(run_id="RUN-TEST-SD2")
    dataset = agent._generate_synthetic_dataset()
    
    for r in dataset.records:
        username = r.get("username", "")
        ssn = r.get("ssn", "")
        
        # Verify reserved test domain
        assert "@example.com" in username or "@test.cfa.local" in username, f"Non-test domain found: {username}"
        
        # Verify reserved test SSN prefix or malformed SSN
        assert ssn.startswith("999-") or ssn == "123-45", f"Non-reserved SSN found: {ssn}"


def test_synthetic_artifacts_created(tmp_path: Path) -> None:
    run_id = "RUN-TEST-SD3"
    agent = TestDataAgent(run_id=run_id)
    agent.artifact_dir = tmp_path
    
    state = AppState(run_id=run_id)
    agent.run(state)
    
    json_path = tmp_path / "synthetic_test_data.json"
    csv_path = tmp_path / "synthetic_test_data.csv"
    
    assert json_path.exists()
    assert csv_path.exists()
    
    json_data = json.loads(json_path.read_text(encoding="utf-8"))
    assert json_data["is_synthetic"] is True
