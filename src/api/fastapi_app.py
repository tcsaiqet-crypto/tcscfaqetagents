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

    if state.understanding and (state.status == "understanding_ready" or state.status == "indexing"):
        return {
            "status": "ready",
            "understanding": state.understanding
        }

    return {
        "status": "running" if state.status == "ai_understanding_running" else state.status,
        "progress": state.progress
    }


@app.get("/", response_class=HTMLResponse)
def serve_react_ui():
    return """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>QET Agent - React Spec-Kit UI</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
  <script src="https://unpkg.com/react@18/umd/react.production.min.js" crossorigin></script>
  <script src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js" crossorigin></script>
  <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
  <script src="https://unpkg.com/lucide@latest"></script>
  <style>
    body { font-family: 'Inter', sans-serif; background-color: #020617; color: #f8fafc; }
    code, pre { font-family: 'JetBrains Mono', monospace; }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen">
  <div id="root"></div>
  <script type="text/babel">
    const { useState, useEffect } = React;

    const API_BASE = '/api/v1';

    function App() {
      const [runId, setRunId] = useState('');
      const [appState, setAppState] = useState(null);
      const [activeTab, setActiveTab] = useState('home');
      const [docFiles, setDocFiles] = useState([]);
      const [zipFile, setZipFile] = useState(null);
      const [statusMsg, setStatusMsg] = useState('');
      const [errorMsg, setErrorMsg] = useState('');
      const [isAnalyzing, setIsAnalyzing] = useState(false);
      const [understanding, setUnderstanding] = useState(null);
      const [errorDiagnostics, setErrorDiagnostics] = useState(null);

      useEffect(() => {
        initRun();
      }, []);

      const initRun = async () => {
        try {
          const res = await fetch(`${API_BASE}/runs`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ project_name: 'CFA Digital Journey' })
          });
          const data = await res.json();
          setRunId(data.run_id);
          setAppState(data.state);
        } catch (err) {
          console.error(err);
        }
      };

      const pollStatus = async () => {
        if (!runId) return;
        try {
          const res = await fetch(`${API_BASE}/runs/${runId}/status`);
          const data = await res.json();
          setAppState(prev => ({
            ...prev,
            status: data.state,
            progress: data.progress,
            error: data.error,
            intake_manifest: data.intake_manifest
          }));
        } catch (err) {
          console.error(err);
        }
      };

      const handleDocUpload = async (e) => {
        if (!e.target.files.length || !runId) return;
        const files = Array.from(e.target.files);
        const formData = new FormData();
        files.forEach(f => formData.append('files', f));

        setStatusMsg('Uploading requirement documents...');
        try {
          const res = await fetch(`${API_BASE}/runs/${runId}/documents`, { method: 'POST', body: formData });
          const data = await res.json();
          setStatusMsg(`Successfully uploaded ${data.uploaded_count} requirement file(s).`);
          pollStatus();
        } catch (err) {
          setErrorMsg('Document upload failed.');
        }
      };

      const handleZipUpload = async (e) => {
        if (!e.target.files.length || !runId) return;
        const file = e.target.files[0];
        if (!file.name.endsWith('.zip')) {
          setErrorMsg('Only .zip files are allowed.');
          return;
        }
        const formData = new FormData();
        formData.append('file', file);

        setStatusMsg('Extracting & indexing codebase ZIP...');
        try {
          const res = await fetch(`${API_BASE}/runs/${runId}/codebase`, { method: 'POST', body: formData });
          const data = await res.json();
          setStatusMsg(`Codebase ZIP uploaded (${data.intake_manifest.total_files} files extracted).`);
          pollStatus();
        } catch (err) {
          setErrorMsg('Codebase ZIP processing failed.');
        }
      };

      const handleStartUnderstanding = async () => {
        if (!runId) return;
        setIsAnalyzing(true);
        setErrorDiagnostics(null);
        try {
          await fetch(`${API_BASE}/runs/${runId}/understanding/start`, { method: 'POST' });
          const interval = setInterval(async () => {
            const res = await fetch(`${API_BASE}/runs/${runId}/understanding`);
            const data = await res.json();
            if (data.status === 'ready') {
              clearInterval(interval);
              setUnderstanding(data.understanding);
              setIsAnalyzing(false);
              pollStatus();
            } else if (data.status === 'failed') {
              clearInterval(interval);
              setErrorDiagnostics(data);
              setIsAnalyzing(false);
              pollStatus();
            }
          }, 1500);
        } catch (err) {
          setIsAnalyzing(false);
          setErrorMsg(err.message);
        }
      };

      const isIntakeReady = Boolean(
        appState?.intake_manifest && 
        (appState.intake_manifest.total_files > 0 || (appState.intake_manifest.doc_files && appState.intake_manifest.doc_files.length > 0))
      );

      return (
        <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
          {/* Header */}
          <header className="sticky top-0 z-50 bg-slate-950/90 backdrop-blur border-b border-slate-800 px-6 py-4 flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-purple-600 flex items-center justify-center font-bold text-white shadow-lg">Q</div>
              <div>
                <h1 className="text-base font-bold bg-gradient-to-r from-slate-100 via-cyan-200 to-purple-300 bg-clip-text text-transparent">QET AI Execution Engine</h1>
                <p className="text-[10px] text-slate-400 font-mono">React-First Spec-Kit Delivery</p>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              <div className="text-xs bg-slate-900 border border-slate-800 px-3 py-1 rounded-lg">
                <span className="text-slate-400">Active Run: </span>
                <code className="text-cyan-300 font-bold">{runId || 'Loading...'}</code>
              </div>
              <button onClick={initRun} className="text-xs text-slate-400 hover:text-cyan-300 underline font-medium">New Run</button>
            </div>
          </header>

          {/* Navigation Ribbon */}
          <div className="bg-slate-900/60 border-b border-slate-800/80 px-6 py-2 flex space-x-2 text-xs font-semibold">
            <button onClick={() => setActiveTab('home')} className={`px-4 py-2 rounded-lg transition-all ${activeTab === 'home' ? 'bg-cyan-950/80 text-cyan-300 border border-cyan-800' : 'text-slate-400 hover:text-slate-200'}`}>
              🏠 1. Home Upload
            </button>
            <button onClick={() => isIntakeReady && setActiveTab('understanding')} disabled={!isIntakeReady} className={`px-4 py-2 rounded-lg transition-all flex items-center space-x-1 ${activeTab === 'understanding' ? 'bg-purple-950/80 text-purple-300 border border-purple-800' : isIntakeReady ? 'text-slate-400 hover:text-slate-200' : 'text-slate-600 opacity-50 cursor-not-allowed'}`}>
              <span>🧠 2. AI Understanding</span>
              {!isIntakeReady && <span className="text-[10px] ml-1">🔒</span>}
            </button>
            {['Test Cases', 'Synthetic Data', 'Playwright Scripts', 'Execution', 'Quality Report'].map((tab, idx) => (
              <button key={idx} disabled className="px-3 py-2 text-slate-600 opacity-50 cursor-not-allowed flex items-center space-x-1">
                <span>{tab}</span>
                <span className="text-[10px]">🔒</span>
              </button>
            ))}
          </div>

          {/* Content Body */}
          <main className="max-w-6xl mx-auto w-full p-6 flex-1 space-y-6">
            {activeTab === 'home' && (
              <div className="space-y-6">
                <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 space-y-3">
                  <h2 className="text-xl font-bold text-slate-100">F01 Home Upload Experience</h2>
                  <p className="text-xs text-slate-400">Upload business requirement documents (.md, .pdf, .txt) and target codebase archive (.zip) to start execution.</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* Doc Upload */}
                  <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 space-y-4">
                    <h3 className="text-sm font-bold text-slate-200">1. Requirement Specifications</h3>
                    <input type="file" multiple accept=".md,.pdf,.txt,.docx" onChange={handleDocUpload} className="block w-full text-xs text-slate-400 bg-slate-950 p-3 rounded-lg border border-slate-800 cursor-pointer" />
                    {appState?.intake_manifest?.doc_files?.length > 0 && (
                      <div className="text-xs text-emerald-400 bg-emerald-950/40 p-3 rounded-lg border border-emerald-800">
                        Uploaded Docs: {appState.intake_manifest.doc_files.join(', ')}
                      </div>
                    )}
                  </div>

                  {/* ZIP Upload */}
                  <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 space-y-4">
                    <h3 className="text-sm font-bold text-slate-200">2. Codebase ZIP Archive</h3>
                    <input type="file" accept=".zip" onChange={handleZipUpload} className="block w-full text-xs text-slate-400 bg-slate-950 p-3 rounded-lg border border-slate-800 cursor-pointer" />
                    {appState?.intake_manifest?.total_files > 0 && (
                      <div className="text-xs text-cyan-400 bg-cyan-950/40 p-3 rounded-lg border border-cyan-800">
                        Extracted {appState.intake_manifest.total_files} codebase files.
                      </div>
                    )}
                  </div>
                </div>

                {/* Status Timeline */}
                <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 space-y-3">
                  <div className="flex justify-between text-xs font-semibold">
                    <span>Lifecycle State: <code className="text-cyan-300 font-bold">{appState?.status || 'idle'}</code></span>
                    <span>Progress: {appState?.progress || 0}%</span>
                  </div>
                  <div className="w-full bg-slate-950 h-2 rounded-full overflow-hidden border border-slate-800">
                    <div className="bg-gradient-to-r from-cyan-500 to-purple-500 h-full transition-all duration-300" style={{ width: `${appState?.progress || 0}%` }}></div>
                  </div>
                </div>

                <div className="flex justify-end">
                  <button onClick={() => setActiveTab('understanding')} disabled={!isIntakeReady} className={`px-6 py-3 rounded-xl text-xs font-bold transition-all ${isIntakeReady ? 'bg-gradient-to-r from-cyan-500 to-purple-600 text-white hover:opacity-90' : 'bg-slate-800 text-slate-500 cursor-not-allowed'}`}>
                    Proceed to Understanding →
                  </button>
                </div>
              </div>
            )}

            {activeTab === 'understanding' && (
              <div className="space-y-6">
                <div className="bg-slate-900/80 border border-slate-800 rounded-2xl p-6 flex justify-between items-center">
                  <div>
                    <h2 className="text-xl font-bold text-slate-100">F02 AI-Required Understanding Engine</h2>
                    <p className="text-xs text-slate-400">Generates structured understanding with AI provenance. Fails fast if AI key or model is invalid.</p>
                  </div>
                  <button onClick={handleStartUnderstanding} disabled={isAnalyzing} className="px-5 py-2.5 rounded-xl text-xs font-bold bg-gradient-to-r from-purple-600 to-indigo-600 hover:opacity-90 text-white">
                    {isAnalyzing ? 'Analyzing with AI...' : 'Start AI Analysis'}
                  </button>
                </div>

                {/* Fail-fast diagnostics surface */}
                {errorDiagnostics && (
                  <div className="bg-rose-950/40 border border-rose-800 rounded-xl p-6 space-y-3 text-xs">
                    <h3 className="font-bold text-rose-300 text-sm">❌ AI Fail-Fast Execution Error</h3>
                    <p className="text-rose-200">Error Code: <code className="font-mono text-white font-bold">{errorDiagnostics.error_code}</code></p>
                    <p className="text-rose-200">{errorDiagnostics.error_message}</p>
                    {errorDiagnostics.diagnostics && (
                      <pre className="bg-slate-950 p-3 rounded text-rose-300 font-mono text-[11px] overflow-x-auto">{JSON.stringify(errorDiagnostics.diagnostics, null, 2)}</pre>
                    )}
                  </div>
                )}

                {/* AI Provenance & Output */}
                {understanding && (
                  <div className="space-y-6">
                    <div className="bg-slate-900/90 border border-slate-800 rounded-xl p-5 space-y-2 text-xs">
                      <h3 className="font-bold text-cyan-300">AI Provenance Metadata</h3>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-1 font-mono">
                        <div><span className="text-slate-500">Provider:</span> {understanding.provenance?.provider}</div>
                        <div><span className="text-slate-500">Model:</span> {understanding.provenance?.model || 'gemini-1.5-flash'}</div>
                        <div><span className="text-slate-500">Fallback Used:</span> <span className="text-indigo-400">{String(understanding.provenance?.fallback_used)}</span></div>
                        <div><span className="text-slate-500">Status:</span> <span className="text-emerald-400">{understanding.validation_status}</span></div>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-2">
                        <h4 className="text-xs font-bold text-slate-400 uppercase">Executive Summary</h4>
                        <p className="text-xs text-slate-200 leading-relaxed">{understanding.summary}</p>
                      </div>
                      <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-2">
                        <h4 className="text-xs font-bold text-slate-400 uppercase">Architecture Notes</h4>
                        <p className="text-xs text-slate-200 leading-relaxed">{understanding.architecture_notes}</p>
                      </div>
                    </div>

                    <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 space-y-3">
                      <h4 className="text-xs font-bold text-slate-400 uppercase">Discovered Components ({understanding.components?.length})</h4>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                        {understanding.components?.map((c, i) => (
                          <div key={i} className="bg-slate-950 p-3 rounded-lg border border-slate-800 text-xs">
                            <span className="font-bold text-indigo-300">{c.name}</span> ({c.type})
                            <p className="text-slate-400 text-[11px] mt-1">{c.description}</p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}
          </main>
        </div>
      );
    }

    ReactDOM.createRoot(document.getElementById('root')).render(<App />);
  </script>
</body>
</html>
"""