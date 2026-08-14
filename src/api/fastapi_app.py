"""FastAPI Runtime Layer exposing REST API contracts for React frontend with UI hosting."""

import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

from schemas.contracts import AppState, ApplicationUnderstanding, IntakeManifest
from src.config import config
from src.services.run_state_service import create_run_state, load_run_state, update_run_status, save_run_state, list_saved_runs
from src.services.ai_settings_store import load_ai_settings_dict, save_ai_settings_dict
from src.services.zip_service import ZipService
from src.agents.understanding_agent import UnderstandingAgent, AIRequiredFailureException
from src.services.llm_service import LLMService
from src.utils.security import SecurityError
from src.utils.logger import logger

app = FastAPI(
    title="QET AI Execution Engine API",
    description="FastAPI Runtime Layer for React-first Home & Understanding flow",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateRunRequest(BaseModel):
    project_name: Optional[str] = "CFA Digital Journey"


class CreateRunResponse(BaseModel):
    run_id: str
    state: AppState


class RunSummary(BaseModel):
    run_id: str
    project_name: str = "CFA Digital Journey"
    status: str
    progress: float
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    total_files: int = 0
    doc_count: int = 0
    has_html_report: bool = False
    has_pdf_report: bool = False
    has_understanding: bool = False


class RunListResponse(BaseModel):
    runs: List[RunSummary]


class DocumentUploadResponse(BaseModel):
    uploaded_count: int
    files: List[str]


class CodebaseUploadResponse(BaseModel):
    intake_manifest: IntakeManifest
    state: AppState


class StatusResponse(BaseModel):
    run_id: str
    state: str
    progress: float
    error: Optional[Dict[str, Any]] = None
    intake_manifest: Optional[IntakeManifest] = None
    stage_timestamps: Dict[str, str] = {}
    launcher_state: Dict[str, Any] = {}


class AIProviderConfig(BaseModel):
    key_present: bool
    display_name: str


class AISettingsResponse(BaseModel):
    active_provider: str
    llm_enabled: bool
    providers: Dict[str, AIProviderConfig]
    runtime_state: Dict[str, Any]
    gemini_candidate_models: List[str] = []


class UpdateAISettingsRequest(BaseModel):
    active_provider: str
    provider_keys: Dict[str, str] = {}


@app.get("/api/v1/health")
def health_check():
    return {"status": "ok", "service": "QET FastAPI Runtime Layer"}


def _build_ai_settings_response() -> AISettingsResponse:
    llm = LLMService()
    active_provider = config.get_active_provider()
    runtime_state = llm.get_runtime_status()
    providers = {
        "gemini": AIProviderConfig(
            key_present=bool(config.get_provider_api_key("gemini")),
            display_name="Google Gemini",
        ),
        "gpt": AIProviderConfig(
            key_present=bool(config.get_provider_api_key("gpt")),
            display_name="OpenAI GPT",
        ),
    }
    gemini_models: List[str] = []
    gemini_key = config.get_provider_api_key("gemini")
    if gemini_key:
        gemini_models = llm.list_gemini_candidates(gemini_key)
    return AISettingsResponse(
        active_provider=active_provider,
        llm_enabled=config.is_llm_enabled(),
        providers=providers,
        runtime_state=runtime_state,
        gemini_candidate_models=gemini_models[:8],
    )


@app.get("/api/v1/ai/settings", response_model=AISettingsResponse)
def get_ai_settings():
    return _build_ai_settings_response()


@app.post("/api/v1/ai/settings", response_model=AISettingsResponse)
def update_ai_settings(req: UpdateAISettingsRequest):
    active_provider = "gpt" if req.active_provider.strip().lower() == "gpt" else "gemini"
    current = load_ai_settings_dict()
    provider_keys = current.get("provider_keys", {}) if isinstance(current, dict) else {}
    if not isinstance(provider_keys, dict):
        provider_keys = {}

    for provider, value in req.provider_keys.items():
        normalized_provider = "gpt" if str(provider).strip().lower() == "gpt" else "gemini"
        clean_value = str(value).strip()
        if clean_value:
            provider_keys[normalized_provider] = clean_value

    save_ai_settings_dict(active_provider=active_provider, provider_keys=provider_keys)
    return _build_ai_settings_response()


@app.get("/api/v1/runs", response_model=RunListResponse)
def list_runs():
    """List all saved historical runs with artifact flags and metrics."""
    runs = list_saved_runs()
    return RunListResponse(runs=[RunSummary(**r) for r in runs])


@app.get("/api/v1/runs/{run_id}", response_model=CreateRunResponse)
def get_run_full_state(run_id: str):
    """Fetch complete AppState for reopening/inspecting a specific historical run."""
    state = load_run_state(run_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return CreateRunResponse(run_id=state.run_id, state=state)


@app.get("/api/v1/runs/{run_id}/reports/{filename}")
def get_run_report_artifact(run_id: str, filename: str):
    """Serve per-run report artifacts (HTML, PDF, JSON)."""
    candidate_paths = [
        Path("uploads") / run_id / "artifacts" / filename,
        Path(__file__).resolve().parents[2] / "uploads" / run_id / "artifacts" / filename,
    ]
    for p in candidate_paths:
        if p.exists():
            media_type = "text/html" if filename.endswith(".html") else ("application/pdf" if filename.endswith(".pdf") else "application/json")
            return FileResponse(str(p), media_type=media_type)
    raise HTTPException(status_code=404, detail=f"Report {filename} not found for run {run_id}")


@app.post("/api/v1/runs", response_model=CreateRunResponse)
def create_run(req: Optional[CreateRunRequest] = None):
    project_name = req.project_name if req else "CFA Digital Journey"
    state = create_run_state(project_name=project_name)
    return CreateRunResponse(run_id=state.run_id, state=state)


@app.post("/api/v1/runs/{run_id}/documents", response_model=DocumentUploadResponse)
async def upload_documents(run_id: str, files: List[UploadFile] = File(...)):
    state = load_run_state(run_id)
    if not state:
        state = create_run_state(run_id=run_id)

    doc_dir = Path("uploads") / run_id / "documents"
    doc_dir.mkdir(parents=True, exist_ok=True)

    saved_filenames = []
    for file in files:
        file_path = doc_dir / file.filename
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        saved_filenames.append(file.filename)

    update_run_status(run_id, status="uploading", progress=30.0)

    state = load_run_state(run_id)
    if state:
        if not state.intake_manifest:
            state.intake_manifest = IntakeManifest(
                upload_id=run_id,
                zip_filename="",
                extracted_path=str(Path("uploads") / run_id / "extracted"),
                total_files=0,
                total_size_bytes=0,
                doc_files=saved_filenames,
                created_at=datetime.now(timezone.utc).isoformat()
            )
        else:
            state.intake_manifest.doc_files = list(set(state.intake_manifest.doc_files + saved_filenames))
        save_run_state(state)

    return DocumentUploadResponse(uploaded_count=len(saved_filenames), files=saved_filenames)


@app.post("/api/v1/runs/{run_id}/codebase", response_model=CodebaseUploadResponse)
async def upload_codebase(run_id: str, file: UploadFile = File(...)):
    state = load_run_state(run_id)
    if not state:
        state = create_run_state(run_id=run_id)

    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip files are supported for codebase upload")

    update_run_status(run_id, status="processing_zip", progress=45.0)

    upload_dir = Path("uploads") / run_id
    upload_dir.mkdir(parents=True, exist_ok=True)
    zip_path = upload_dir / file.filename

    with open(zip_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
      zip_service = ZipService(target_dir=Path("uploads"))
      zip_result = zip_service.process_zip_upload(run_id, zip_path, file.filename)

      # Support both legacy (manifest only) and enhanced (manifest + summary) service contracts.
      if isinstance(zip_result, tuple) and len(zip_result) == 2:
        manifest, zip_processing = zip_result
      else:
        manifest = zip_result
        zip_processing = {"status": "not_available"}
    except Exception as e:
        error_code = "zip_validation_failed" if isinstance(e, SecurityError) else "zip_extraction_failed"
        err = {"error_code": error_code, "error_message": str(e), "diagnostics": {"file": file.filename}}
        update_run_status(run_id, status="error", progress=45.0, error=err)
        raise HTTPException(status_code=400, detail=err)

    state = load_run_state(run_id)
    if state and state.intake_manifest and state.intake_manifest.doc_files:
        manifest.doc_files = list(set(manifest.doc_files + state.intake_manifest.doc_files))

    state.intake_manifest = manifest
    state.launcher_state["zip_processing"] = zip_processing
    save_run_state(state)
    update_run_status(run_id, status="indexing", progress=60.0)

    state = load_run_state(run_id)
    return CodebaseUploadResponse(intake_manifest=manifest, state=state)


@app.get("/api/v1/runs/{run_id}/status", response_model=StatusResponse)
def get_run_status(run_id: str):
    state = load_run_state(run_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    return StatusResponse(
        run_id=run_id,
        state=state.status,
        progress=state.progress,
        error=state.last_error,
        intake_manifest=state.intake_manifest,
      stage_timestamps=state.stage_timestamps,
      launcher_state=state.launcher_state,
    )


def _execute_understanding_task(run_id: str):
    state = load_run_state(run_id)
    if not state:
        return
    update_run_status(run_id, status="ai_understanding_running", progress=75.0)
    agent = UnderstandingAgent(run_id=run_id)
    try:
        updated_state, provenance = agent.run_ai_required(state)
        
        # Run categorizer stage if active
        if config.features.enable_requirement_categorization:
            from src.agents.requirement_categorizer import RequirementCategorizer
            categorizer = RequirementCategorizer(run_id=run_id)
            if not categorizer.llm.is_enabled():
                updated_state = categorizer.run(updated_state)
            else:
                updated_state, cat_prov = categorizer.run_ai_required(updated_state)

        save_run_state(updated_state)
        update_run_status(run_id, status="understanding_ready", progress=100.0)
    except AIRequiredFailureException as e:
        err_payload = {
            "error_code": e.error_code,
            "error_message": e.error_message,
            "diagnostics": e.diagnostics,
            "retryable": True
        }
        update_run_status(run_id, status="error", progress=75.0, error=err_payload)
    except Exception as e:
        err_payload = {
            "error_code": "understanding_execution_error",
            "error_message": str(e),
            "diagnostics": {"exception": str(e)},
            "retryable": True
        }
        update_run_status(run_id, status="error", progress=75.0, error=err_payload)


@app.post("/api/v1/runs/{run_id}/understanding/start")
def start_understanding(run_id: str, background_tasks: BackgroundTasks):
    state = load_run_state(run_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    update_run_status(run_id, status="ai_understanding_running", progress=75.0)
    background_tasks.add_task(_execute_understanding_task, run_id)
    return {"status": "started", "run_id": run_id}


@app.get("/api/v1/runs/{run_id}/understanding")
def get_understanding(run_id: str):
    state = load_run_state(run_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    if state.status == "error" or state.last_error:
        err = state.last_error or {
            "error_code": "unknown_error",
            "error_message": "Understanding analysis failed",
            "diagnostics": {},
            "retryable": True
        }
        return {
            "status": "failed",
            "error_code": err.get("error_code", "failed"),
            "error_message": err.get("error_message", "Understanding stage failed"),
            "diagnostics": err.get("diagnostics", {}),
            "retryable": err.get("retryable", True)
        }

    if state.understanding and state.status == "understanding_ready":
        return {
            "status": "ready",
            "understanding": state.understanding
        }

    return {
        "status": "running" if state.status == "ai_understanding_running" else state.status,
        "progress": state.progress
    }

@app.get("/api/v1/runs/{run_id}/coverage")
def get_requirement_coverage(run_id: str):
    state = load_run_state(run_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
        
    und = state.understanding
    if not und or not getattr(und, "requirements", None):
        return {
            "run_id": run_id,
            "total_requirements": 0,
            "covered_requirements": 0,
            "coverage_percentage": 0.0,
            "categories": [],
            "requirements": []
        }
        
    # Get all test cases
    test_cases = []
    if state.test_suite and state.test_suite.test_cases:
        test_cases = state.test_suite.test_cases
        
    # Map requirements to test cases
    req_to_cases = {}
    for tc in test_cases:
        req_id = tc.requirement_id
        if req_id:
            req_to_cases[req_id] = req_to_cases.get(req_id, [])
            req_to_cases[req_id].append(tc.case_id)
            
    reqs_out = []
    covered_count = 0
    for req in und.requirements:
        mapped = req_to_cases.get(req.requirement_id, [])
        is_covered = len(mapped) > 0
        if is_covered:
            covered_count += 1
            
        reqs_out.append({
            "requirement_id": req.requirement_id,
            "title": req.title,
            "description": req.description,
            "type": req.type,
            "category_id": req.category_id,
            "source_evidence": req.source_evidence,
            "confidence": req.confidence,
            "is_covered": is_covered,
            "mapped_test_cases": mapped
        })
        
    # Categories coverage
    categories_out = []
    for cat in und.requirement_categories:
        cat_reqs = [r for r in reqs_out if r["category_id"] == cat.category_id]
        cat_total = len(cat_reqs)
        cat_covered = sum(1 for r in cat_reqs if r["is_covered"])
        cat_percentage = (cat_covered / cat_total * 100.0) if cat_total > 0 else 100.0
        
        categories_out.append({
            "category_id": cat.category_id,
            "name": cat.name,
            "type": cat.type,
            "description": cat.description,
            "total_requirements": cat_total,
            "covered_requirements": cat_covered,
            "coverage_percentage": round(cat_percentage, 1),
            "requirements": cat_reqs
        })
        
    total_reqs = len(und.requirements)
    overall_percentage = (covered_count / total_reqs * 100.0) if total_reqs > 0 else 0.0
    
    return {
        "run_id": run_id,
        "total_requirements": total_reqs,
        "covered_requirements": covered_count,
        "coverage_percentage": round(overall_percentage, 1),
        "categories": categories_out,
        "requirements": reqs_out
    }

from fastapi.staticfiles import StaticFiles
import os

# Resolve dist directory path across the layouts this API can be launched from:
# __file__ is backend/src/api/fastapi_app.py
# parents[2] is backend/, parents[3] is the repo root (where `npm run build` outputs dist/)
_dist_candidates = [
    Path(__file__).resolve().parents[2] / "dist",
    Path(__file__).resolve().parents[3] / "dist",
    Path(__file__).resolve().parents[3] / "qet-react-ui" / "dist",
]
dist_path = next((p for p in _dist_candidates if p.exists() and os.listdir(p)), _dist_candidates[0])

if dist_path.exists() and os.listdir(dist_path):
    logger.info(f"Serving static production React build from {dist_path}")
    app.mount("/", StaticFiles(directory=str(dist_path), html=True), name="static")
else:
    logger.info("React production build not detected at dist/. Serving API health check at root.")


@app.get("/", response_class=HTMLResponse)
def serve_vanilla_spa():
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0, minimum-scale=0.5, maximum-scale=5.0, user-scalable=yes" />
  <title>QET Agent Studio</title>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg-color: #020617;
      --text-color: #f1f5f9;
      --header-bg: rgba(2, 6, 23, 0.8);
      --header-border: #1e293b;
      --card-bg: #0f172a;
      --card-border: #1e293b;
      --muted-text: #94a3b8;
      --cyan-glow: rgba(6, 182, 212, 0.15);
      --purple-glow: rgba(168, 85, 247, 0.15);
      --tab-active-bg: #1e1b4b;
      --tab-active-text: #c084fc;
      --tab-active-border: #682773;
    }
    
    .light {
      --bg-color: #f8fafc;
      --text-color: #0f172a;
      --header-bg: rgba(255, 255, 255, 0.9);
      --header-border: #e2e8f0;
      --card-bg: #ffffff;
      --card-border: #e2e8f0;
      --muted-text: #64748b;
      --cyan-glow: rgba(6, 182, 212, 0.05);
      --purple-glow: rgba(168, 85, 247, 0.05);
      --tab-active-bg: #eff6ff;
      --tab-active-text: #1d4ed8;
      --tab-active-border: #bfdbfe;
    }

    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Inter', sans-serif;
      background-color: var(--bg-color);
      color: var(--text-color);
      transition: background-color 0.2s, color 0.2s;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }
    
    header {
      position: sticky;
      top: 0;
      z-index: 50;
      backdrop-filter: blur(8px);
      background-color: var(--header-bg);
      border-bottom: 1px solid var(--header-border);
      padding: 1rem 1.5rem;
      display: flex;
      align-items: center;
      justify-content: space-between;
    }

    .header-logo {
      display: flex;
      align-items: center;
      gap: 0.75rem;
    }

    .logo-badge {
      width: 2rem;
      height: 2rem;
      border-radius: 0.5rem;
      background: linear-gradient(135deg, #06b6d4, #8b5cf6);
      display: flex;
      align-items: center;
      justify-content: center;
      font-weight: 800;
      color: white;
      box-shadow: 0 4px 12px rgba(6, 182, 212, 0.3);
    }

    .header-title h1 {
      font-size: 1rem;
      font-weight: 700;
      background: linear-gradient(to right, #22d3ee, #a78bfa);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
    }

    .header-title p {
      font-size: 0.65rem;
      font-family: 'JetBrains Mono', monospace;
      color: var(--muted-text);
    }

    .header-actions {
      display: flex;
      align-items: center;
      gap: 1rem;
    }

    .run-badge {
      font-size: 0.75rem;
      padding: 0.25rem 0.75rem;
      border-radius: 0.5rem;
      background-color: var(--card-bg);
      border: 1px solid var(--card-border);
      font-family: 'JetBrains Mono', monospace;
    }

    .run-badge span { color: var(--muted-text); }
    .run-badge code { color: #22d3ee; font-weight: 700; }

    .theme-btn {
      padding: 0.5rem 1rem;
      border-radius: 0.5rem;
      border: 1px solid var(--card-border);
      background-color: var(--card-bg);
      color: var(--text-color);
      font-size: 0.75rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s;
    }

    .theme-btn:hover {
      opacity: 0.9;
    }

    .tab-ribbon {
      border-bottom: 1px solid var(--header-border);
      background-color: var(--header-bg);
      padding: 0.5rem 1.5rem;
      display: flex;
      gap: 0.5rem;
      overflow-x: auto;
    }

    .tab-btn {
      padding: 0.5rem 1rem;
      border-radius: 0.5rem;
      border: 1px solid transparent;
      background: transparent;
      color: var(--muted-text);
      font-size: 0.75rem;
      font-weight: 600;
      cursor: pointer;
      display: flex;
      align-items: center;
      gap: 0.25rem;
      transition: all 0.2s;
    }

    .tab-btn.active {
      background-color: var(--tab-active-bg);
      color: var(--tab-active-text);
      border-color: var(--tab-active-border);
    }

    .tab-btn:disabled {
      opacity: 0.35;
      cursor: not-allowed;
    }
    
    /* Coverage Matrix Styles */
    section#sect-coverage {
      display: none;
      flex-direction: column;
      gap: 1.5rem;
    }
    
    section#sect-coverage.active {
      display: flex;
    }

    main {
      max-width: 1200px;
      width: 100%;
      margin: 0 auto;
      padding: 1.5rem;
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 1.5rem;
    }

    .toast {
      padding: 0.75rem 1rem;
      border-radius: 0.5rem;
      border: 1px solid #1e1b4b;
      background-color: #0c0a09;
      color: #a78bfa;
      font-size: 0.75rem;
      display: none;
    }

    .toast.error {
      background-color: #450a0a;
      border-color: #7f1d1d;
      color: #fca5a5;
    }

    .hero-panel {
      border: 1px solid var(--card-border);
      border-radius: 1rem;
      padding: 1.5rem;
      background-color: var(--card-bg);
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .hero-panel h2 { font-size: 1.25rem; font-weight: 700; }
    .hero-panel p { font-size: 0.75rem; color: var(--muted-text); }

    .upload-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 1.5rem;
    }

    @media (min-width: 768px) {
      .upload-grid { grid-template-columns: 1fr 1fr; }
    }

    .upload-card {
      border: 1px solid var(--card-border);
      border-radius: 0.75rem;
      padding: 1.5rem;
      background-color: var(--card-bg);
      display: flex;
      flex-direction: column;
      justify-content: space-between;
      gap: 1rem;
      transition: all 0.2s;
    }

    .upload-card.dragging {
      border-color: #22d3ee;
      background-color: var(--cyan-glow);
    }

    .card-info h3 { font-size: 0.875rem; font-weight: 700; margin-bottom: 0.25rem; }
    .card-info.docs h3 { color: #22d3ee; }
    .card-info.zip h3 { color: #a78bfa; }
    .card-info p { font-size: 0.75rem; color: var(--muted-text); }

    .drop-zone-label {
      display: block;
      width: 100%;
      text-align: center;
      font-size: 0.75rem;
      font-weight: 600;
      padding: 2rem 1rem;
      border: 1px dashed var(--card-border);
      border-radius: 0.5rem;
      cursor: pointer;
      background-color: rgba(0, 0, 0, 0.15);
      transition: all 0.2s;
    }

    .drop-zone-label:hover {
      background-color: rgba(0, 0, 0, 0.25);
    }

    .file-input { display: none; }

    .file-badge-list {
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .file-badge {
      font-size: 0.75rem;
      font-family: 'JetBrains Mono', monospace;
      padding: 0.5rem;
      border-radius: 0.5rem;
      border: 1px solid var(--card-border);
      background-color: rgba(0,0,0,0.2);
    }

    .progress-panel {
      border: 1px solid var(--card-border);
      border-radius: 0.75rem;
      padding: 1.5rem;
      background-color: var(--card-bg);
      display: flex;
      flex-direction: column;
      gap: 1rem;
    }

    .progress-header {
      display: flex;
      justify-content: space-between;
      font-size: 0.75rem;
      font-weight: 700;
    }

    .progress-bar-bg {
      width: 100%;
      height: 0.5rem;
      border-radius: 0.25rem;
      background-color: rgba(0,0,0,0.3);
      border: 1px solid var(--card-border);
      overflow: hidden;
    }

    .progress-bar-fill {
      height: 100%;
      background: linear-gradient(to right, #06b6d4, #6366f1, #a855f7);
      width: 0%;
      transition: width 0.3s;
    }

    .btn-primary {
      padding: 0.75rem 1.5rem;
      border-radius: 0.75rem;
      border: none;
      background: linear-gradient(to right, #06b6d4, #8b5cf6);
      color: white;
      font-size: 0.75rem;
      font-weight: 700;
      cursor: pointer;
      box-shadow: 0 4px 12px rgba(6, 182, 212, 0.2);
      transition: all 0.2s;
    }

    .btn-primary:hover:not(:disabled) {
      opacity: 0.9;
      transform: translateY(-1px);
    }

    .btn-primary:disabled {
      opacity: 0.4;
      cursor: not-allowed;
      box-shadow: none;
    }

    footer {
      border-top: 1px solid var(--header-border);
      padding: 1.5rem;
      text-align: center;
      font-size: 0.75rem;
      color: var(--muted-text);
      background-color: var(--card-bg);
    }

    section { display: none; flex-direction: column; gap: 1.5rem; }
    section.active { display: flex; }

    /* AI Understanding styles */
    .diagnostics-box {
      background-color: rgba(69, 10, 10, 0.4);
      border: 1px solid #991b1b;
      border-radius: 0.75rem;
      padding: 1.5rem;
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
      font-size: 0.75rem;
    }

    .diagnostics-box h3 { color: #fca5a5; font-size: 0.875rem; }
    .diagnostics-box code { background-color: rgba(0,0,0,0.3); padding: 0.125rem 0.375rem; border-radius: 0.25rem; color: white; }
    .diagnostics-box pre { background-color: #020617; padding: 0.75rem; border-radius: 0.5rem; border: 1px solid #7f1d1d; overflow-x: auto; font-size: 0.7rem; color: #fca5a5; }

    .provenance-card {
      border: 1px solid var(--card-border);
      border-radius: 0.75rem;
      padding: 1.25rem;
      background-color: var(--card-bg);
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
      font-size: 0.75rem;
    }

    .provenance-card h3 {
      font-size: 0.65rem;
      font-weight: 800;
      color: #06b6d4;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    .provenance-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 0.75rem;
      font-family: 'JetBrains Mono', monospace;
    }

    @media (min-width: 768px) {
      .provenance-grid { grid-template-columns: repeat(4, 1fr); }
    }

    .text-grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 1.5rem;
    }

    @media (min-width: 768px) {
      .text-grid { grid-template-columns: 1fr 1fr; }
    }

    .text-card {
      border: 1px solid var(--card-border);
      border-radius: 0.75rem;
      padding: 1.25rem;
      background-color: var(--card-bg);
      display: flex;
      flex-direction: column;
      gap: 0.5rem;
    }

    .text-card h4 { font-size: 0.75rem; font-weight: 700; color: var(--muted-text); text-transform: uppercase; }
    .text-card p { font-size: 0.75rem; line-height: 1.5; }

    .component-inventory {
      border: 1px solid var(--card-border);
      border-radius: 0.75rem;
      padding: 1.25rem;
      background-color: var(--card-bg);
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
    }

    .component-inventory h4 { font-size: 0.75rem; font-weight: 700; color: var(--muted-text); text-transform: uppercase; }
    .comp-grid { display: grid; grid-template-columns: 1fr; gap: 0.75rem; }
    @media (min-width: 640px) {
      .comp-grid { grid-template-columns: 1fr 1fr; }
    }

    .comp-item {
      padding: 0.75rem;
      border-radius: 0.5rem;
      border: 1px solid var(--card-border);
      background-color: rgba(0,0,0,0.1);
      font-size: 0.75rem;
    }

    .comp-name { font-weight: 700; color: #818cf8; }
    .comp-desc { font-size: 0.7rem; color: var(--muted-text); margin-top: 0.25rem; }
  </style>
</head>
<body>

  <header>
    <div class="header-logo">
      <div class="logo-badge">Q</div>
      <div class="header-title">
        <h1>QET Agent Studio</h1>
        <p>Offline-safe vanilla platform</p>
      </div>
    </div>
    
    <div class="header-actions">
      <div class="run-badge">
        <span>Active Run: </span>
        <code id="active-run-id">Initializing...</code>
      </div>
      <div style="display: flex; align-items: center; gap: 0.25rem;">
        <button id="zoom-out-btn" class="theme-btn" style="padding: 0.5rem 0.75rem;" title="Zoom Out">ðŸ”Žâž–</button>
        <span id="zoom-val" style="font-size: 0.75rem; font-family: monospace; min-width: 2.5rem; text-align: center;">100%</span>
        <button id="zoom-in-btn" class="theme-btn" style="padding: 0.5rem 0.75rem;" title="Zoom In">ðŸ”Žâž•</button>
      </div>
      <button id="theme-btn" class="theme-btn">â˜€ï¸ Light</button>
      <button id="reset-run-btn" class="theme-btn" style="color:#06b6d4; border-color:transparent;">Reset Run</button>
    </div>
  </header>

  <div class="tab-ribbon">
    <button id="tab-home-btn" class="tab-btn active">ðŸ  1. Home Upload</button>
    <button id="tab-understanding-btn" class="tab-btn" disabled>ðŸ§  2. AI Understanding ðŸ”’</button>
    <button class="tab-btn" disabled>Test Cases ðŸ”’</button>
    <button class="tab-btn" disabled>Synthetic Data ðŸ”’</button>
    <button class="tab-btn" disabled>Playwright Scripts ðŸ”’</button>
  </div>

  <main>
    <div id="toast" class="toast">Status update...</div>

    <!-- Section 1: Home Upload -->
    <section id="sect-home" class="active">
      <div class="hero-panel">
        <h2>F01 Home Upload Experience</h2>
        <p>Create a workspace run, upload business requirement documents, and upload codebase ZIP packages. Drag-and-drop zones are active below.</p>
      </div>

      <div class="upload-grid">
        <!-- Docs Upload Card -->
        <div id="drop-docs" class="upload-card">
          <div class="card-info docs">
            <h3>1. Requirement Specifications</h3>
            <p>Drag & Drop files here, or click upload button below.</p>
          </div>
          <label class="drop-zone-label">
            Select Document Files (.md, .pdf, .txt)
            <input type="file" id="file-docs" class="file-input" multiple accept=".md,.pdf,.txt,.docx" />
          </label>
          <div id="doc-files-list" class="file-badge-list"></div>
        </div>

        <!-- ZIP Upload Card -->
        <div id="drop-zip" class="upload-card">
          <div class="card-info zip">
            <h3>2. Codebase ZIP Archive</h3>
            <p>Drag & Drop codebase .zip archive here, or click to upload.</p>
          </div>
          <label class="drop-zone-label">
            Select ZIP Archive (.zip)
            <input type="file" id="file-zip" class="file-input" accept=".zip" />
          </label>
          <div id="zip-files-list" class="file-badge-list"></div>
        </div>
      </div>

      <div class="progress-panel">
        <div class="progress-header">
          <span>Runtime Stage: <code id="stage-label" style="color:#06b6d4;">idle</code></span>
          <span id="progress-percentage">Progress: 0%</span>
        </div>
        <div class="progress-bar-bg">
          <div id="progress-bar-fill" class="progress-bar-fill"></div>
        </div>
      </div>

      <div style="display:flex; justify-content:flex-end;">
        <button id="proceed-btn" class="btn-primary" disabled>Proceed to Understanding Tab â†’</button>
      </div>
    </section>

    <!-- Section 2: AI Understanding -->
    <section id="sect-understanding">
      <div class="hero-panel" style="display:flex; flex-direction:row; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:1rem;">
        <div>
          <h2>F02 AI-Required Understanding Engine</h2>
          <p>Generates structured understanding with AI provenance. Fails fast if AI key or model is invalid.</p>
        </div>
        <button id="start-analysis-btn" class="btn-primary">Start AI Analysis</button>
      </div>

      <div id="diagnostics-panel" class="diagnostics-box" style="display:none;">
        <h3 id="diag-title">âŒ AI Fail-Fast Execution Error</h3>
        <p>Error Code: <code id="diag-code">unknown_error</code></p>
        <p id="diag-msg">Connection failed.</p>
        <pre id="diag-details">{}</pre>
      </div>

      <div id="understanding-results" style="display:none; flex-direction:column; gap:1.5rem;">
        <div class="provenance-card">
          <h3>AI Output Provenance Audit</h3>
          <div class="provenance-grid">
            <div><span style="color:var(--muted-text)">Provider:</span> <span id="prov-provider">gemini</span></div>
            <div><span style="color:var(--muted-text)">Model:</span> <span id="prov-model">gemini-1.5-flash</span></div>
            <div><span style="color:var(--muted-text)">Fallback Used:</span> <span id="prov-fallback" style="color:#818cf8">false</span></div>
            <div><span style="color:var(--muted-text)">Validation:</span> <span id="prov-validation" style="color:#34d399">VALIDATED</span></div>
          </div>
        </div>

        <div class="text-grid">
          <div class="text-card">
            <h4>Executive Summary</h4>
            <p id="result-summary">No summary loaded.</p>
          </div>
          <div class="text-card">
            <h4>Architecture Notes</h4>
            <p id="result-arch">No architecture notes loaded.</p>
          </div>
        </div>

        <div class="component-inventory">
          <h4>Discovered UI Components</h4>
          <div id="result-comps" class="comp-grid"></div>
        </div>
      </div>
    </section>
  </main>

  <footer>
    <p>QET Agent Studio &bull; Spec-Kit 004 Corrective Pass &bull; Antigravity Platform</p>
  </footer>

  <script>
    // Zoom scaling controls
    let uiScale = 1.0;
    const zoomInBtn = document.getElementById('zoom-in-btn');
    const zoomOutBtn = document.getElementById('zoom-out-btn');
    const zoomVal = document.getElementById('zoom-val');

    function updateZoom() {
      document.body.style.zoom = uiScale;
      zoomVal.innerText = Math.round(uiScale * 100) + '%';
    }

    zoomInBtn.addEventListener('click', () => {
      if (uiScale < 1.8) {
        uiScale += 0.1;
        updateZoom();
      }
    });

    zoomOutBtn.addEventListener('click', () => {
      if (uiScale > 0.6) {
        uiScale -= 0.1;
        updateZoom();
      }
    });

    // Theme toggle
    const themeBtn = document.getElementById('theme-btn');
    themeBtn.addEventListener('click', () => {
      document.body.classList.toggle('light');
      if (document.body.classList.contains('light')) {
        themeBtn.innerText = 'ðŸŒ™ Dark';
      } else {
        themeBtn.innerText = 'â˜€ï¸ Light';
      }
    });

    // Run context variables
    const API_BASE = '/api/v1';
    let runId = '';
    let appState = null;
    let isIntakeReady = false;

    // Toast helpers
    const toast = document.getElementById('toast');
    function showToast(msg, isError = false) {
      toast.innerText = msg;
      toast.style.display = 'block';
      if (isError) {
        toast.classList.add('error');
      } else {
        toast.classList.remove('error');
      }
    }

    // Initialize run ID on page load
    async function initRun() {
      try {
        const res = await fetch(API_BASE + '/runs', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ project_name: 'CFA Digital Journey' })
        });
        const data = await res.json();
        runId = data.run_id;
        appState = data.state;
        document.getElementById('active-run-id').innerText = runId;
        showToast('Fresh execution run initialized: ' + runId);
        updateProgressUI(0, 'idle');
      } catch (err) {
        showToast('Failed to initialize workspace run.', true);
      }
    }

    // Update Stage & Progress indicators
    function updateProgressUI(progress, status) {
      document.getElementById('stage-label').innerText = status;
      document.getElementById('progress-percentage').innerText = 'Progress: ' + progress + '%';
      document.getElementById('progress-bar-fill').style.width = progress + '%';
    }

    // Status Poller
    async function pollStatus() {
      if (!runId) return;
      try {
        const res = await fetch(API_BASE + '/runs/' + runId + '/status');
        const data = await res.json();
        
        appState = data;
        updateProgressUI(data.progress, data.state);

        // Update file lists if manifest exists
        if (data.intake_manifest) {
          const manifest = data.intake_manifest;
          
          // Render Docs list
          const docsList = document.getElementById('doc-files-list');
          if (manifest.doc_files && manifest.doc_files.length > 0) {
            docsList.innerHTML = manifest.doc_files.map(f => `<div class="file-badge">ðŸ“„ ${f}</div>`).join('');
          } else {
            docsList.innerHTML = '';
          }

          // Render ZIP status
          const zipList = document.getElementById('zip-files-list');
          if (manifest.total_files > 0) {
            zipList.innerHTML = `<div class="file-badge" style="border-color:#a78bfa;">ðŸ“¦ ZIP Extracted (${manifest.total_files} files)</div>`;
          } else {
            zipList.innerHTML = '';
          }

          // Check if intake ready
          isIntakeReady = Boolean(manifest.total_files > 0 || (manifest.doc_files && manifest.doc_files.length > 0));
          const proceedBtn = document.getElementById('proceed-btn');
          const tabBtn = document.getElementById('tab-understanding-btn');
          if (isIntakeReady) {
            proceedBtn.removeAttribute('disabled');
            tabBtn.removeAttribute('disabled');
            tabBtn.innerHTML = 'ðŸ§  2. AI Understanding';
          } else {
            proceedBtn.setAttribute('disabled', 'true');
            tabBtn.setAttribute('disabled', 'true');
            tabBtn.innerHTML = 'ðŸ§  2. AI Understanding ðŸ”’';
          }
        }
      } catch (err) {
        console.error('Poller error:', err);
      }
    }

    // Set polling interval
    setInterval(() => {
      const activeStates = ['uploading', 'processing_zip', 'indexing', 'ai_understanding_running'];
      if (appState && activeStates.indexOf(appState.status) !== -1) {
        pollStatus();
      }
    }, 2000);

    // Tab Navigation
    const tabs = {
      'home': { btn: document.getElementById('tab-home-btn'), sect: document.getElementById('sect-home') },
      'understanding': { btn: document.getElementById('tab-understanding-btn'), sect: document.getElementById('sect-understanding') },
      'coverage': { btn: document.getElementById('tab-coverage-btn'), sect: document.getElementById('sect-coverage') }
    };

    function switchTab(target) {
      Object.keys(tabs).forEach(k => {
        tabs[k].btn.classList.remove('active');
        tabs[k].sect.classList.remove('active');
      });
      tabs[target].btn.classList.add('active');
      tabs[target].sect.classList.add('active');
    }

    tabs.home.btn.addEventListener('click', () => switchTab('home'));
    tabs.understanding.btn.addEventListener('click', () => switchTab('understanding'));
    tabs.coverage.btn.addEventListener('click', () => switchTab('coverage'));
    document.getElementById('proceed-btn').addEventListener('click', () => switchTab('understanding'));
    document.getElementById('reset-run-btn').addEventListener('click', () => initRun());

    // File Selector & Upload Handlers
    const fileDocs = document.getElementById('file-docs');
    fileDocs.addEventListener('change', (e) => {
      if (e.target.files.length > 0) {
        uploadDocuments(Array.from(e.target.files));
      }
    });

    const fileZip = document.getElementById('file-zip');
    fileZip.addEventListener('change', (e) => {
      if (e.target.files.length > 0) {
        uploadCodebaseZip(e.target.files[0]);
      }
    });

    // Upload Documents
    async function uploadDocuments(files) {
      if (!runId) return;
      const formData = new FormData();
      files.forEach(f => formData.append('files', f));
      showToast('Uploading requirement documents...');
      try {
        const res = await fetch(API_BASE + '/runs/' + runId + '/documents', {
          method: 'POST',
          body: formData
        });
        const data = await res.json();
        showToast('Successfully uploaded ' + data.uploaded_count + ' requirement file(s).');
        pollStatus();
      } catch (err) {
        showToast('Failed to upload requirement documents.', true);
      }
    }

    // Upload Codebase ZIP
    async function uploadCodebaseZip(file) {
      if (!runId) return;
      if (!file.name.endsWith('.zip')) {
        showToast('Only ZIP archive formats (.zip) are supported for codebases.', true);
        return;
      }
      const formData = new FormData();
      formData.append('file', file);
      showToast('Uploading and indexing codebase ZIP package...');
      try {
        const res = await fetch(API_BASE + '/runs/' + runId + '/codebase', {
          method: 'POST',
          body: formData
        });
        const data = await res.json();
        showToast('Codebase ZIP uploaded and indexed successfully.');
        pollStatus();
      } catch (err) {
        showToast('Failed to process codebase ZIP upload.', true);
      }
    }

    // Setup Drag-and-Drop Event Listeners
    function setupDragAndDrop(dropAreaId, onFilesDropped) {
      const dropArea = document.getElementById(dropAreaId);
      
      dropArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropArea.classList.add('dragging');
      });

      dropArea.addEventListener('dragleave', () => {
        dropArea.classList.remove('dragging');
      });

      dropArea.addEventListener('drop', (e) => {
        e.preventDefault();
        dropArea.classList.remove('dragging');
        if (e.dataTransfer.files.length > 0) {
          onFilesDropped(e.dataTransfer.files);
        }
      });
    }

    setupDragAndDrop('drop-docs', (files) => uploadDocuments(Array.from(files)));
    setupDragAndDrop('drop-zip', (files) => uploadCodebaseZip(files[0]));

    // AI Analysis Start button handler
    const startBtn = document.getElementById('start-analysis-btn');
    startBtn.addEventListener('click', async () => {
      if (!runId) return;
      startBtn.setAttribute('disabled', 'true');
      startBtn.innerText = 'Analyzing codebase...';
      document.getElementById('diagnostics-panel').style.display = 'none';
      document.getElementById('understanding-results').style.display = 'none';

      try {
        await fetch(API_BASE + '/runs/' + runId + '/understanding/start', { method: 'POST' });
        
        // Poll for AI results
        const interval = setInterval(async () => {
          const res = await fetch(API_BASE + '/runs/' + runId + '/understanding');
          const data = await res.json();
          
          if (data.status === 'ready') {
            clearInterval(interval);
            startBtn.removeAttribute('disabled');
            startBtn.innerText = 'Start AI Analysis';
            renderUnderstanding(data.understanding);
            pollStatus();
          } else if (data.status === 'failed') {
            clearInterval(interval);
            startBtn.removeAttribute('disabled');
            startBtn.innerText = 'Start AI Analysis';
            renderDiagnostics(data);
            pollStatus();
          }
        }, 1500);
      } catch (err) {
        startBtn.removeAttribute('disabled');
        startBtn.innerText = 'Start AI Analysis';
        showToast('Failed to start AI Analysis.', true);
      }
    });

    // Render Diagnostics Errors
    function renderDiagnostics(data) {
      document.getElementById('diagnostics-panel').style.display = 'flex';
      document.getElementById('diag-code').innerText = data.error_code || 'unknown_error';
      document.getElementById('diag-msg').innerText = data.error_message || 'AI engine failed.';
      document.getElementById('diag-details').innerText = JSON.stringify(data.diagnostics || {}, null, 2);
    }

    // Render AI Results
    
    async function fetchCoverage() {
      if (!runId) return;
      try {
        const res = await fetch(API_BASE + '/runs/' + runId + '/coverage');
        const data = await res.json();
        
        document.getElementById('coverage-percentage-val').innerText = data.coverage_percentage + '%';
        document.getElementById('coverage-bar-fill').style.width = data.coverage_percentage + '%';
        document.getElementById('total-requirements-val').innerText = data.total_requirements;
        
        const list = document.getElementById('coverage-categories-list');
        if (data.categories && data.categories.length > 0) {
          list.innerHTML = data.categories.map(cat => `
            <div class="upload-card" style="display:flex; flex-direction:column; gap:0.75rem;">
              <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid var(--card-border); padding-bottom:0.5rem;">
                <h4 style="font-size:0.9rem; font-weight:600;">${cat.name} (${cat.type})</h4>
                <div style="font-size:0.75rem; font-family:monospace; background:#292524; padding:0.25rem 0.5rem; border-radius:0.25rem;">
                  Coverage: ${cat.covered_requirements}/${cat.total_requirements} (${cat.coverage_percentage}%)
                </div>
              </div>
              <p style="font-size:0.7rem; color:var(--muted-text);">${cat.description}</p>
              <div style="display:flex; flex-direction:column; gap:0.5rem; margin-top:0.5rem;">
                ${cat.requirements.map(req => `
                  <div style="display:flex; justify-content:space-between; align-items:center; background:#1c1917; padding:0.5rem; border-radius:0.35rem; font-size:0.7rem;">
                    <div style="max-width:70%;">
                      <strong style="color:#06b6d4;">${req.requirement_id}: ${req.title}</strong>
                      <p style="color:var(--muted-text); font-size:0.65rem; margin-top:0.15rem;">${req.description}</p>
                      <p style="font-size:0.6rem; color:#a8a29e; margin-top:0.25rem;">Evidence: <code>${req.source_evidence}</code> (Confidence: ${req.confidence})</p>
                    </div>
                    <div style="display:flex; flex-direction:column; align-items:end; gap:0.25rem;">
                      ${req.is_covered 
                        ? `<span style="background:#065f46; color:#34d399; font-weight:600; padding:0.15rem 0.4rem; border-radius:0.25rem; font-size:0.6rem;"> Covered</span>`
                        : `<span style="background:#78350f; color:#fbbf24; font-weight:600; padding:0.15rem 0.4rem; border-radius:0.25rem; font-size:0.6rem;"> Uncovered</span>`
                      }
                      ${req.mapped_test_cases && req.mapped_test_cases.length > 0
                        ? `<span style="font-size:0.6rem; color:var(--muted-text);">Tests: ${req.mapped_test_cases.join(', ')}</span>`
                        : ''
                      }
                    </div>
                  </div>
                `).join('')}
              </div>
            </div>
          `).join('');
        } else {
          list.innerHTML = '<p style="font-size:0.75rem; color:var(--muted-text)">No requirement categories mapped yet.</p>';
        }
      } catch (err) {
        console.error('Error fetching coverage:', err);
      }
    }


    function renderUnderstanding(und) {
      document.getElementById('understanding-results').style.display = 'flex';
      document.getElementById('prov-provider').innerText = und.provenance ? und.provenance.provider : 'gemini';
      document.getElementById('prov-model').innerText = (und.provenance && und.provenance.model) || 'gemini-1.5-flash';
      document.getElementById('prov-fallback').innerText = und.provenance ? und.provenance.fallback_used : 'false';
      document.getElementById('prov-validation').innerText = und.validation_status || 'VALIDATED';

      document.getElementById('result-summary').innerText = und.summary || 'No summary.';
      document.getElementById('result-arch').innerText = und.architecture_notes || 'No architecture notes.';

      // Components Grid
      const compGrid = document.getElementById('result-comps');
      if (und.components && und.components.length > 0) {
        compGrid.innerHTML = und.components.map(c => `
          <div class="comp-item">
            <span class="comp-name">${c.name}</span> (${c.type})
            <p class="comp-desc">${c.description}</p>
          </div>
        `).join('');
      } else {
        compGrid.innerHTML = '<p style="font-size:0.75rem; color:var(--muted-text)">No components found.</p>';
      }
    }

    // Start execution run on load
    initRun();
  </script>
</body>
</html>
"""

