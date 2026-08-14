"""Persistence helpers for saving and restoring AppState per run."""

import uuid
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone

from src.models.schemas import AppState


def _get_uploads_dirs() -> List[Path]:
    """Return search directories for run uploads in order of priority."""
    dirs = [Path("uploads")]
    parent_uploads = Path(__file__).resolve().parents[2] / "uploads"
    if parent_uploads.exists() and parent_uploads not in dirs:
        dirs.append(parent_uploads)
    return dirs


def _run_state_path(run_id: str) -> Path:
    # Check if existing run exists in any uploads dir
    for base in _get_uploads_dirs():
        candidate = base / run_id / "app_state.json"
        if candidate.exists():
            return candidate
    return Path("uploads") / run_id / "app_state.json"


def save_run_state(state: AppState) -> Path:
    path = _run_state_path(state.run_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(state.model_dump_json(indent=2), encoding="utf-8")
    return path


def load_run_state(run_id: str) -> Optional[AppState]:
    path = _run_state_path(run_id)
    if not path.exists():
        return None
    try:
        return AppState.model_validate_json(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def create_run_state(run_id: Optional[str] = None, project_name: str = "CFA Digital Journey") -> AppState:
    if not run_id:
        timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        short_id = uuid.uuid4().hex[:6].upper()
        run_id = f"RUN-{timestamp_str}-{short_id}"
    
    state = AppState(
        run_id=run_id,
        project_name=project_name,
        status="idle",
        progress=0.0,
        stage_timestamps={"created_at": datetime.now(timezone.utc).isoformat()}
    )
    save_run_state(state)
    return state


def update_run_status(
    run_id: str,
    status: str,
    progress: float = 0.0,
    error: Optional[Dict[str, Any]] = None
) -> AppState:
    state = load_run_state(run_id)
    if not state:
        state = create_run_state(run_id=run_id)
    
    state.status = status
    state.progress = progress
    state.stage_timestamps[status] = datetime.now(timezone.utc).isoformat()
    
    if error:
        state.last_error = error
        state.errors.append(f"[{status}] {error.get('error_message', 'Unknown error')}")
    
    save_run_state(state)
    return state


def list_saved_runs() -> List[Dict[str, Any]]:
    """Enumerate all saved run directories and return sorted summaries."""
    seen_ids = set()
    runs = []

    for base_dir in _get_uploads_dirs():
        if not base_dir.exists():
            continue
        for run_dir in base_dir.iterdir():
            if not run_dir.is_dir() or not run_dir.name.startswith("RUN-"):
                continue
            run_id = run_dir.name
            if run_id in seen_ids:
                continue
            
            state_file = run_dir / "app_state.json"
            artifacts_dir = run_dir / "artifacts"
            
            project_name = "CFA Digital Journey"
            status = "idle"
            progress = 0.0
            created_at = None
            updated_at = None
            total_files = 0
            doc_count = 0
            has_understanding = False

            if state_file.exists():
                try:
                    data = json.loads(state_file.read_text(encoding="utf-8"))
                    project_name = data.get("project_name", project_name)
                    status = data.get("status", status)
                    progress = float(data.get("progress", progress))
                    timestamps = data.get("stage_timestamps", {})
                    created_at = timestamps.get("created_at")
                    if timestamps:
                        updated_at = max(timestamps.values())
                    manifest = data.get("intake_manifest") or {}
                    total_files = manifest.get("total_files", 0)
                    doc_count = len(manifest.get("doc_files", []))
                    has_understanding = bool(data.get("understanding"))
                except Exception:
                    pass

            if not created_at:
                try:
                    created_at = datetime.fromtimestamp(run_dir.stat().st_ctime, tz=timezone.utc).isoformat()
                except Exception:
                    created_at = datetime.now(timezone.utc).isoformat()
            if not updated_at:
                try:
                    updated_at = datetime.fromtimestamp(run_dir.stat().st_mtime, tz=timezone.utc).isoformat()
                except Exception:
                    updated_at = created_at

            has_html_report = (artifacts_dir / "quality_report.html").exists()
            has_pdf_report = (artifacts_dir / "quality_report.pdf").exists()
            if (artifacts_dir / "application_understanding.json").exists():
                has_understanding = True

            seen_ids.add(run_id)
            runs.append({
                "run_id": run_id,
                "project_name": project_name,
                "status": status,
                "progress": progress,
                "created_at": created_at,
                "updated_at": updated_at,
                "total_files": total_files,
                "doc_count": doc_count,
                "has_html_report": has_html_report,
                "has_pdf_report": has_pdf_report,
                "has_understanding": has_understanding,
            })

    # Sort descending by updated_at or created_at
    runs.sort(key=lambda r: r.get("updated_at") or r.get("created_at") or "", reverse=True)
    return runs
