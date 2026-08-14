"""FastAPI Runtime Layer exposing REST API contracts for React frontend with UI hosting."""

import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from schemas.contracts import AppState, ApplicationUnderstanding, IntakeManifest
from src.services.run_state_service import create_run_state, load_run_state, update_run_status, save_run_state
from src.services.zip_service import ZipService
from src.agents.understanding_agent import UnderstandingAgent, AIRequiredFailureException
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


@app.get("/api/v1/health")
def health_check():
    return {"status": "ok", "service": "QET FastAPI Runtime Layer"}


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
        manifest = zip_service.process_zip_upload(run_id, zip_path, file.filename)
    except Exception as e:
        err = {"error_code": "zip_extraction_failed", "error_message": str(e), "diagnostics": {"file": file.filename}}
        update_run_status(run_id, status="error", progress=45.0, error=err)
        raise HTTPException(status_code=400, detail=f"Failed to extract codebase ZIP: {str(e)}")

    state = load_run_state(run_id)
    if state and state.intake_manifest and state.intake_manifest.doc_files:
        manifest.doc_files = list(set(manifest.doc_files + state.intake_manifest.doc_files))

    state.intake_manifest = manifest
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
        stage_timestamps=state.stage_timestamps
    )


def _execute_understanding_task(run_id: str):
    state = load_run_state(run_id)
    if not state:
        return
    update_run_status(run_id, status="ai_understanding_running", progress=75.0)
    agent = UnderstandingAgent(run_id=run_id)
    try:
        updated_state, provenance = agent.run_ai_required(state)
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

from fastapi.staticfiles import StaticFiles
import os

# Resolve dist directory path
# __file__ is backend/src/api/fastapi_app.py
# parents[2] is backend/
dist_path = Path(__file__).resolve().parents[2] / "dist"
if not dist_path.exists():
    # Also check sibling directories if running from QET agents
    dist_path = Path(__file__).resolve().parents[3] / "qet-react-ui" / "dist"

if dist_path.exists() and os.listdir(dist_path):
    logger.info(f"Serving static production React build from {dist_path}")
    app.mount("/", StaticFiles(directory=str(dist_path), html=True), name="static")
else:
    logger.info("React production build not detected at dist/. Serving API health check at root.")
    @app.get("/", response_class=HTMLResponse)
    def serve_api_welcome():
        return """
        <html>
        <head><title>QET API Layer</title></head>
        <body style="font-family: sans-serif; background-color: #0f172a; color: #f1f5f9; padding: 2rem;">
            <h2>QET FastAPI Runtime Layer Active</h2>
            <p>API endpoints are available at <code>/api/v1/*</code>.</p>
            <p>To view the React UI, please run the dev server or build the frontend:</p>
            <pre style="background-color: #020617; padding: 1rem; border-radius: 8px; color: #38bdf8;">
cd qet-react-ui
npm install
npm run dev (dev server on port 5173)
# or
npm run build (build production bundle to host directly from FastAPI on port 8000)
            </pre>
        </body>
        </html>
        """
