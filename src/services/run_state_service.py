"""Persistence helpers for saving and restoring AppState per run."""

import uuid
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from src.models.schemas import AppState


def _run_state_path(run_id: str) -> Path:
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
