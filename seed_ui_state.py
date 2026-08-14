import zipfile
from pathlib import Path

from schemas.contracts import AppState, ExecutionMode, ExecutionRequest
from src.services.zip_service import ZipService
from src.services.run_state_service import save_run_state
from src.agents.understanding_agent import UnderstandingAgent
from src.agents.test_data_agent import TestDataAgent
from src.agents.playwright_agent import PlaywrightAgent
from src.agents.accessibility_agent import AccessibilityAgent
from src.agents.report_agent import ReportAgent
from src.services.execution_engine import ExecutionEngine

run_id = "RUN-20260813-001"

zip_path = Path("uploads") / f"{run_id}_ui_seed_source.zip"
zip_path.parent.mkdir(parents=True, exist_ok=True)
src_root = Path("sample_test_target_app")
with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
    for file_path in src_root.rglob("*"):
        if file_path.is_file() and "__pycache__" not in file_path.parts and file_path.suffix != ".db":
            zf.write(file_path, file_path.relative_to(src_root))

manifest = ZipService().process_zip_upload(run_id, zip_path, zip_path.name)
state = AppState(run_id=run_id, project_name="Sample Test Target App (UI seed)", intake_manifest=manifest)

state = UnderstandingAgent(run_id=run_id).run(state)
state = TestDataAgent(run_id=run_id).run(state)
state = PlaywrightAgent(run_id=run_id).run(state)
state = AccessibilityAgent(run_id=run_id).run(state)

engine = ExecutionEngine(run_id=run_id)
req = ExecutionRequest(execution_id=f"exec-{run_id}", mode=ExecutionMode.PLAYWRIGHT_UI, explicit_user_approval=True)
result = engine.execute(req, is_non_production_confirmed=True, is_script_reviewed=True)
state.last_execution_result = result
print("execution status:", result.status)

state = ReportAgent(run_id=run_id).run(state)
save_run_state(state)
print("Seeded run state for", run_id)
