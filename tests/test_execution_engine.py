"""Unit tests for ExecutionEngine, host validation, gate checks, and failure classification."""

import json
import pytest
from pathlib import Path
from schemas.contracts import ExecutionMode, ExecutionRequest, ExecutionStatus
from src.services.execution_engine import ExecutionEngine, ExecutionNotAllowedError


def test_is_mode_enabled() -> None:
    engine = ExecutionEngine()
    
    # Playwright UI must be enabled
    assert engine.is_mode_enabled(ExecutionMode.PLAYWRIGHT_UI) is True
    
    # All other execution modes must be disabled in V1
    assert engine.is_mode_enabled(ExecutionMode.URL_EXECUTION) is False
    assert engine.is_mode_enabled(ExecutionMode.API_TESTING) is False
    assert engine.is_mode_enabled(ExecutionMode.PERFORMANCE_TESTING) is False
    assert engine.is_mode_enabled(ExecutionMode.ACCESSIBILITY_EXECUTION) is False
    assert engine.is_mode_enabled(ExecutionMode.SECURITY_SCANNING) is False


@pytest.mark.parametrize("mode", [
    ExecutionMode.URL_EXECUTION,
    ExecutionMode.API_TESTING,
    ExecutionMode.PERFORMANCE_TESTING,
    ExecutionMode.ACCESSIBILITY_EXECUTION,
    ExecutionMode.SECURITY_SCANNING,
])
def test_disabled_modes_raise_error(mode: ExecutionMode) -> None:
    engine = ExecutionEngine()
    req = ExecutionRequest(
        execution_id="exec_test",
        mode=mode,
        explicit_user_approval=True
    )
    
    with pytest.raises(ExecutionNotAllowedError, match="strictly disabled in Version 1"):
        engine.validate_request(req)


def test_production_domain_rejection() -> None:
    engine = ExecutionEngine()
    
    # Production host keywords strictly blocked
    with pytest.raises(PermissionError, match="forbidden production keyword"):
        engine.validate_target_host("https://cfa.com/login")

    with pytest.raises(PermissionError, match="forbidden production keyword"):
        engine.validate_target_host("https://production-cfa-app.com")


def test_host_mismatch_rejection(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = ExecutionEngine()
    monkeypatch.setattr(engine, "allowed_host", "localhost")
    
    with pytest.raises(PermissionError, match="does not match allowed host policy"):
        engine.validate_target_host("http://other-staging-host.com")


def test_playwright_execution_requires_all_gates() -> None:
    engine = ExecutionEngine()
    req = ExecutionRequest(
        execution_id="exec_ui_1",
        mode=ExecutionMode.PLAYWRIGHT_UI,
        explicit_user_approval=True
    )

    # Reject if non-production target unconfirmed
    with pytest.raises(PermissionError, match="non-production target confirmation is required"):
        engine.validate_request(req, is_non_production_confirmed=False, is_script_reviewed=True)

    # Reject if script review unconfirmed
    with pytest.raises(PermissionError, match="scripts must be reviewed"):
        engine.validate_request(req, is_non_production_confirmed=True, is_script_reviewed=False)

    # Reject if user approval missing
    req_unapproved = ExecutionRequest(execution_id="exec_ui_2", mode=ExecutionMode.PLAYWRIGHT_UI, explicit_user_approval=False)
    with pytest.raises(PermissionError, match="requires explicit user approval"):
        engine.validate_request(req_unapproved, is_non_production_confirmed=True, is_script_reviewed=True)


def test_failure_classification_taxonomy() -> None:
    engine = ExecutionEngine()
    
    assert engine.classify_failure("Element not found with locator data-testid='username'") == "selector_defect"
    assert engine.classify_failure("Timeout 30000ms exceeded waiting for element") == "timing_issue"
    assert engine.classify_failure("AssertionError: Expected 'Dashboard' got 'Login'") == "application_defect"
    assert engine.classify_failure("KeyError: missing 'ssn' key in json dataset") == "data_defect"
    assert engine.classify_failure("Connection Refused 500 Internal Server Error") == "environment_defect"
    assert engine.classify_failure("SyntaxError: invalid syntax in test script") == "test_defect"


def test_approved_playwright_execution_stores_evidence(tmp_path: Path) -> None:
    run_id = "RUN-TEST-EXEC"
    engine = ExecutionEngine(run_id=run_id)
    engine.artifact_dir = tmp_path
    
    req_approved = ExecutionRequest(
        execution_id="exec_ui_3",
        mode=ExecutionMode.PLAYWRIGHT_UI,
        explicit_user_approval=True
    )
    
    result = engine.execute(req_approved, is_non_production_confirmed=True, is_script_reviewed=True)
    assert result.execution_id == "exec_ui_3"
    assert result.status in [ExecutionStatus.PASSED, ExecutionStatus.NOT_RUN, ExecutionStatus.FAILED]
    
    evidence_path = tmp_path / "execution_evidence.json"
    assert evidence_path.exists()
