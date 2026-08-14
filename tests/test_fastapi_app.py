"""Tests for FastAPI Runtime Layer, state persistence, and failfast AI understanding."""

import io
import pytest
from fastapi.testclient import TestClient

from src.api.fastapi_app import app
from src.services.run_state_service import load_run_state
from src.agents.understanding_agent import AIRequiredFailureException, UnderstandingAgent
from schemas.contracts import AppState

client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    # Serves the built React app (dist/) when present, else the vanilla fallback/health text.
    assert "<div id=\"root\">" in response.text or "QET API Layer" in response.text or "QET Agent" in response.text

    health_resp = client.get("/api/v1/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] == "ok"


def test_create_run():
    response = client.post("/api/v1/runs", json={"project_name": "Test Project"})
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert data["state"]["status"] == "idle"
    
    saved_state = load_run_state(data["run_id"])
    assert saved_state is not None
    assert saved_state.project_name == "Test Project"


def test_upload_documents_and_status():
    run_resp = client.post("/api/v1/runs", json={"project_name": "Doc Test"})
    run_id = run_resp.json()["run_id"]

    files = [
        ("files", ("test_req.md", b"# Requirements\nFeature 1 spec", "text/markdown"))
    ]
    doc_resp = client.post(f"/api/v1/runs/{run_id}/documents", files=files)
    assert doc_resp.status_code == 200
    assert doc_resp.json()["uploaded_count"] == 1
    assert "test_req.md" in doc_resp.json()["files"]

    status_resp = client.get(f"/api/v1/runs/{run_id}/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["state"] == "uploading"
    assert status_data["progress"] == 30.0


def test_upload_codebase_zip_validation():
    run_resp = client.post("/api/v1/runs", json={"project_name": "ZIP Test"})
    run_id = run_resp.json()["run_id"]

    bad_files = [("file", ("code.txt", b"not a zip", "text/plain"))]
    resp = client.post(f"/api/v1/runs/{run_id}/codebase", files=bad_files)
    assert resp.status_code == 400
    assert "Only .zip files" in resp.json()["detail"]


def test_understanding_ai_failfast_when_no_key(monkeypatch: pytest.MonkeyPatch):
    run_resp = client.post("/api/v1/runs", json={"project_name": "Failfast Test"})
    run_id = run_resp.json()["run_id"]

    from src.config import config
    monkeypatch.setattr(type(config), "get_provider_api_key", lambda self, provider: "")

    agent = UnderstandingAgent(run_id=run_id)

    state = load_run_state(run_id)
    with pytest.raises(AIRequiredFailureException) as exc_info:
        agent.run_ai_required(state)

    assert exc_info.value.error_code == "provider_key_missing"
    assert exc_info.value.diagnostics is not None


def test_ai_settings_round_trip():
    get_resp = client.get("/api/v1/ai/settings")
    assert get_resp.status_code == 200
    initial = get_resp.json()
    assert initial["active_provider"] in ["gemini", "gpt"]
    assert "providers" in initial

    save_resp = client.post(
        "/api/v1/ai/settings",
        json={
            "active_provider": "gpt",
            "provider_keys": {"gpt": "test-openai-key", "gemini": "test-gemini-key"},
        },
    )
    assert save_resp.status_code == 200
    saved = save_resp.json()
    assert saved["active_provider"] == "gpt"
    assert saved["providers"]["gpt"]["key_present"] is True
    assert saved["providers"]["gemini"]["key_present"] is True


def test_get_requirement_coverage_endpoint():
    run_resp = client.post("/api/v1/runs", json={"project_name": "Coverage API Test"})
    run_id = run_resp.json()["run_id"]

    # Initial state should return empty lists
    coverage_resp = client.get(f"/api/v1/runs/{run_id}/coverage")
    assert coverage_resp.status_code == 200
    data = coverage_resp.json()
    assert data["total_requirements"] == 0
    assert data["coverage_percentage"] == 0.0
    assert len(data["categories"]) == 0
    assert len(data["requirements"]) == 0



def test_get_requirement_coverage_endpoint_with_seeded_state():
    """G4: Validate coverage endpoint math when requirements and test cases are non-empty.

    Seeds a run state with:
    - 3 requirements across 2 categories (Security, Functional)
    - 2 test cases mapped to the first 2 requirements
    Then asserts exact coverage counts, percentages, mapped_test_cases, and category-level math.
    """
    from src.services.run_state_service import save_run_state, load_run_state
    from schemas.contracts import (
        AppState,
        ApplicationUnderstanding,
        ApplicationComponent,
        Requirement,
        RequirementCategory,
        RequirementType,
        TestSuite,
        TestCase,
    )

    # Create a new run
    run_resp = client.post("/api/v1/runs", json={"project_name": "Coverage Seeded Test"})
    assert run_resp.status_code == 200
    run_id = run_resp.json()["run_id"]

    # Build seeded requirements
    req_auth = Requirement(
        requirement_id="REQ-AUTH-01",
        title="Secure Login",
        description="JWT-based login must be enforced",
        type=RequirementType.Security,
        category_id="CAT-SEC",
        source_evidence="Login.tsx",
    )
    req_upload = Requirement(
        requirement_id="REQ-UPLOAD-01",
        title="Document Upload",
        description="Accept PDF/DOCX uploads up to 10 MB",
        type=RequirementType.Functional,
        category_id="CAT-FUNC",
        source_evidence="Upload.tsx",
    )
    req_flow = Requirement(
        requirement_id="REQ-FLOW-01",
        title="Application Submission",
        description="End-to-end loan application flow",
        type=RequirementType.Functional,
        category_id="CAT-FUNC",
        source_evidence="pipeline.py",
    )

    cat_sec = RequirementCategory(
        category_id="CAT-SEC",
        name="Security Controls",
        type=RequirementType.Security,
        description="Security requirement catalog group",
        requirements=[req_auth],
    )
    cat_func = RequirementCategory(
        category_id="CAT-FUNC",
        name="Functional Verification",
        type=RequirementType.Functional,
        description="Functional requirement catalog group",
        requirements=[req_upload, req_flow],
    )

    # Map 2 test cases to REQ-AUTH-01 and REQ-UPLOAD-01; REQ-FLOW-01 stays uncovered
    tc1 = TestCase(
        case_id="TC-AUTH-001",
        title="Login with valid credentials",
        feature_area="Authentication",
        description="Happy path login test",
        preconditions=["User account exists"],
        steps=["Navigate to /login", "Enter credentials", "Click Login"],
        expected_result="Redirect to dashboard",
        case_type="Positive",
        priority="High",
        requirement_id="REQ-AUTH-01",
        requirement_category_id="CAT-SEC",
        requirement_type="Security",
    )
    tc2 = TestCase(
        case_id="TC-UPLOAD-001",
        title="Upload valid PDF",
        feature_area="Document Upload",
        description="Happy path upload test",
        preconditions=["User is logged in"],
        steps=["Click Upload", "Select PDF < 10 MB", "Confirm"],
        expected_result="File accepted and listed",
        case_type="Positive",
        priority="Medium",
        requirement_id="REQ-UPLOAD-01",
        requirement_category_id="CAT-FUNC",
        requirement_type="Functional",
    )

    # Load and mutate state
    state = load_run_state(run_id)
    assert state is not None

    und = ApplicationUnderstanding(
        summary="CFA Loan Application",
        architecture_notes="React + FastAPI",
        components=[],
        requirements=[req_auth, req_upload, req_flow],
        requirement_categories=[cat_sec, cat_func],
    )
    state.understanding = und
    state.test_suite = TestSuite(suite_id="TS-G4-001", name="G4 Coverage Test Suite", description="Seeded test suite for G4 coverage endpoint verification", test_cases=[tc1, tc2])
    save_run_state(state)

    # Call coverage endpoint
    coverage_resp = client.get(f"/api/v1/runs/{run_id}/coverage")
    assert coverage_resp.status_code == 200
    data = coverage_resp.json()

    # --- Top-level coverage math ---
    assert data["total_requirements"] == 3
    assert data["covered_requirements"] == 2       # REQ-AUTH-01 + REQ-UPLOAD-01
    assert data["coverage_percentage"] == 66.7     # round(2/3*100, 1)

    # --- Per-requirement mapped_test_cases ---
    req_map = {r["requirement_id"]: r for r in data["requirements"]}
    assert req_map["REQ-AUTH-01"]["is_covered"] is True
    assert "TC-AUTH-001" in req_map["REQ-AUTH-01"]["mapped_test_cases"]

    assert req_map["REQ-UPLOAD-01"]["is_covered"] is True
    assert "TC-UPLOAD-001" in req_map["REQ-UPLOAD-01"]["mapped_test_cases"]

    assert req_map["REQ-FLOW-01"]["is_covered"] is False
    assert req_map["REQ-FLOW-01"]["mapped_test_cases"] == []

    # --- Category-level math ---
    cat_map = {c["category_id"]: c for c in data["categories"]}

    # CAT-SEC: 1 req, 1 covered => 100%
    assert cat_map["CAT-SEC"]["total_requirements"] == 1
    assert cat_map["CAT-SEC"]["covered_requirements"] == 1
    assert cat_map["CAT-SEC"]["coverage_percentage"] == 100.0

    # CAT-FUNC: 2 reqs, 1 covered => 50%
    assert cat_map["CAT-FUNC"]["total_requirements"] == 2
    assert cat_map["CAT-FUNC"]["covered_requirements"] == 1
    assert cat_map["CAT-FUNC"]["coverage_percentage"] == 50.0

