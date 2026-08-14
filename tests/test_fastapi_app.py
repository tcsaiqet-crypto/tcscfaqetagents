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
    assert "QET API Layer" in response.text or "QET Agent" in response.text

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


def test_understanding_ai_failfast_when_no_key():
    run_resp = client.post("/api/v1/runs", json={"project_name": "Failfast Test"})
    run_id = run_resp.json()["run_id"]

    agent = UnderstandingAgent(run_id=run_id)

    state = load_run_state(run_id)
    with pytest.raises(AIRequiredFailureException) as exc_info:
        agent.run_ai_required(state)

    assert exc_info.value.error_code in ["provider_key_missing", "provider_disabled", "invalid_model_json", "model_timeout", "schema_validation_failed"]
    assert exc_info.value.diagnostics is not None
