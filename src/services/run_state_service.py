"""Persistence helpers for saving and restoring AppState per run."""

from pathlib import Path
from typing import Optional

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
