"""Tests for AppState persistence helpers."""

from src.models.schemas import AppState
from src.services.run_state_service import load_run_state, save_run_state


def test_save_and_load_run_state_round_trip(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)

    state = AppState(run_id="RUN-TEST-PERSIST")
    state.errors = ["sample error"]

    path = save_run_state(state)
    assert path.exists()

    loaded = load_run_state("RUN-TEST-PERSIST")
    assert loaded is not None
    assert loaded.run_id == state.run_id
    assert loaded.errors == ["sample error"]


def test_load_run_state_missing_file_returns_none(tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    assert load_run_state("RUN-NOT-FOUND") is None
