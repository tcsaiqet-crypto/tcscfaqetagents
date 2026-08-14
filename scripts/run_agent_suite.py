"""CLI helper that runs the QET agent suite against a given codebase (folder or .zip).

Used by run_agent_suite.ps1 -- see that script for the one setting you normally
need to change (the source path).
"""

import argparse
import os
import sys
import time
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ORIGINAL_CWD = Path.cwd()
sys.path.insert(0, str(REPO_ROOT))
os.chdir(REPO_ROOT)  # keep uploads/ and workspace/ paths anchored regardless of invocation cwd

from schemas.contracts import AppState, ExecutionMode, ExecutionRequest  # noqa: E402
from src.agents.accessibility_agent import AccessibilityAgent  # noqa: E402
from src.agents.playwright_agent import PlaywrightAgent  # noqa: E402
from src.agents.report_agent import ReportAgent  # noqa: E402
from src.agents.test_case_agent import TestCaseAgent  # noqa: E402
from src.agents.test_data_agent import TestDataAgent  # noqa: E402
from src.agents.understanding_agent import AIRequiredFailureException, UnderstandingAgent  # noqa: E402
from src.services.execution_engine import ExecutionEngine  # noqa: E402
from src.services.zip_service import ZipService  # noqa: E402


def build_zip(source: Path, run_id: str) -> Path:
    """Return a ready-to-upload zip: pass zips through, package folders on the fly."""
    if source.suffix.lower() == ".zip":
        return source

    zip_path = Path("uploads") / f"{run_id}_source.zip"
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file_path in source.rglob("*"):
            if file_path.is_file() and "__pycache__" not in file_path.parts and file_path.suffix != ".db":
                zf.write(file_path, file_path.relative_to(source))
    return zip_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the QET agent suite against a target source path.")
    parser.add_argument("--source", required=True, help="Folder or .zip of the codebase to analyze/test.")
    parser.add_argument("--run-id", default=None, help="Run ID (default: auto-generated).")
    args = parser.parse_args()

    source = Path(args.source)
    if not source.is_absolute():
        source = ORIGINAL_CWD / source  # resolve relative to the caller's cwd, not the repo root
    source = source.resolve()
    if not source.exists():
        print(f"ERROR: source path does not exist: {source}")
        return 1

    run_id = args.run_id or f"RUN-CLI-{int(time.time())}"
    print(f"Run ID: {run_id}")
    print(f"Source: {source}")

    zip_path = build_zip(source, run_id)
    manifest = ZipService().process_zip_upload(run_id, zip_path, zip_path.name)
    state = AppState(run_id=run_id, project_name=source.name, intake_manifest=manifest)

    print("\n== Understanding ==")
    state = UnderstandingAgent(run_id=run_id).run(state)
    print(f"fallback_used: {state.understanding.fallback_used}")

    print("\n== Test Cases ==")
    try:
        state = TestCaseAgent(run_id=run_id).run(state)
        print(f"test cases: {len(state.test_suite.test_cases)}")
    except AIRequiredFailureException as exc:
        print(f"skipped (AI provider required): {exc.error_code} -- {exc.error_message}")

    print("\n== Test Data ==")
    state = TestDataAgent(run_id=run_id).run(state)
    print(f"synthetic records: {len(state.synthetic_dataset.records)}")

    print("\n== Playwright ==")
    state = PlaywrightAgent(run_id=run_id).run(state)
    print(f"playwright scripts: {len(state.playwright_scripts)}")

    print("\n== Accessibility ==")
    try:
        state = AccessibilityAgent(run_id=run_id).run(state)
        report = state.accessibility_report
        print(
            f"rating: {report.rating}  rules passed: {report.rules_passed}/{report.rules_total}  "
            f"files scanned: {report.files_scanned}  violations: {report.total_violations} "
            f"(critical={report.critical_count} serious={report.serious_count} "
            f"moderate={report.moderate_count} minor={report.minor_count})"
        )
    except Exception as exc:
        print(f"skipped (accessibility scan failed): {exc}")

    print("\n== Execution ==")
    engine = ExecutionEngine(run_id=run_id)
    request = ExecutionRequest(
        execution_id=f"exec-{run_id}",
        mode=ExecutionMode.PLAYWRIGHT_UI,
        explicit_user_approval=True,
    )
    result = engine.execute(request, is_non_production_confirmed=True, is_script_reviewed=True)
    state.last_execution_result = result
    print(f"status: {result.status.value}  passed: {result.passed_count}  failed: {result.failed_count}")
    if result.failure_summary:
        print(f"failure_summary: {result.failure_summary}")

    print("\n== Report ==")
    state = ReportAgent(run_id=run_id).run(state)
    print(f"html report: {state.latest_report.html_report_path}")
    print(f"pdf report:  {state.latest_report.pdf_report_path}")

    print(f"\nArtifacts: uploads/{run_id}/artifacts/")
    return 0 if result.status.value == "passed" else 2


if __name__ == "__main__":
    raise SystemExit(main())
