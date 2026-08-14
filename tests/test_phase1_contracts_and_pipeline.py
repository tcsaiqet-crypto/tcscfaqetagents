"""Unit tests for Phase 1 contract hardening and pipeline validation."""

import pytest
from src.models.schemas import (
    AppState,
    IntakeManifest,
    FileMetadata,
    ApplicationUnderstanding,
    TestSuite,
    TestCase,
    SyntheticDataset,
    PlaywrightScript,
    ExecutionResult,
    QualityReport,
)
from src.workflows.pipeline import SequentialQETPipeline


def test_appstate_hardened_fields_initialization():
    """Verify AppState initializes Phase 1 metadata tracking fields."""
    state = AppState()
    assert isinstance(state.stage_timestamps, dict)
    assert isinstance(state.stage_validation, dict)
    assert isinstance(state.stage_provenance, dict)
    assert isinstance(state.launcher_state, dict)
    assert isinstance(state.execution_evidence_index, dict)


def test_stage_models_provenance_and_validation_fields():
    """Verify stage models carry explicit provenance, validation, and upstream traceability fields."""
    und = ApplicationUnderstanding(
        summary="Test summary",
        architecture_notes="Test arch",
        provenance={"provider": "gemini-1.5-flash", "prompt_version": "v1.0"},
        validation_status="VALIDATED",
        fallback_used=False,
    )
    assert und.provenance["provider"] == "gemini-1.5-flash"
    assert und.validation_status == "VALIDATED"
    assert und.fallback_used is False

    case = TestCase(
        case_id="TC-001",
        title="Valid Login",
        feature_area="Auth",
        description="Verify valid login",
        expected_result="Login successful",
        provenance={"generator": "TestCaseAgent"},
        upstream_ids=["COMP-001"],
        validation_status="VALIDATED",
    )
    assert case.upstream_ids == ["COMP-001"]
    assert case.validation_status == "VALIDATED"

    suite = TestSuite(
        suite_id="SUITE-001",
        name="Main Suite",
        description="Suite description",
        test_cases=[case],
        provenance={"generator": "TestCaseAgent"},
        validation_status="VALIDATED",
    )
    assert suite.validation_status == "VALIDATED"

    ds = SyntheticDataset(
        dataset_id="DS-001",
        dataset_name="Test Data",
        data_schema={"username": "str"},
        records=[{"username": "test_user"}],
        upstream_case_ids=["TC-001"],
        synthetic_only_validated=True,
    )
    assert ds.upstream_case_ids == ["TC-001"]
    assert ds.synthetic_only_validated is True

    script = PlaywrightScript(
        script_id="SCR-001",
        test_case_id="TC-001",
        filename="test_login.py",
        code="print('test')",
        upstream_case_ids=["TC-001"],
        selector_confidence_map={"username": "High"},
    )
    assert script.selector_confidence_map["username"] == "High"


def test_pipeline_records_stage_timestamps_and_validation(tmp_path):
    """Verify pipeline records timestamps, validation status, and provenance on stage run."""
    manifest = IntakeManifest(
        upload_id="RUN-TEST-001",
        zip_filename="test.zip",
        extracted_path=str(tmp_path),
        total_files=2,
        total_size_bytes=1024,
        files=[FileMetadata(rel_path="src/app.py", size_bytes=500, extension=".py")],
        doc_files=[],
        created_at="2026-08-14T00:00:00Z",
    )
    state = AppState(intake_manifest=manifest)
    pipeline = SequentialQETPipeline()

    state = pipeline.run(state)

    assert "Understanding" in state.stage_timestamps
    assert state.stage_validation["Understanding"] == "VALIDATED"
    assert "Understanding" in state.stage_provenance

    assert "Test Cases" in state.stage_timestamps
    assert state.stage_validation["Test Cases"] == "VALIDATED"

    assert "Test Data" in state.stage_timestamps
    assert state.stage_validation["Test Data"] == "VALIDATED"

    assert "Playwright" in state.stage_timestamps
    assert state.stage_validation["Playwright"] == "VALIDATED"

    assert "Report" in state.stage_timestamps
    assert state.stage_validation["Report"] == "VALIDATED"


def test_pipeline_downstream_reset_clears_metadata(tmp_path):
    """Verify retrying an upstream stage clears downstream outputs and tracking metadata."""
    manifest = IntakeManifest(
        upload_id="RUN-TEST-002",
        zip_filename="test.zip",
        extracted_path=str(tmp_path),
        total_files=1,
        total_size_bytes=100,
        files=[FileMetadata(rel_path="app.py", size_bytes=100, extension=".py")],
        doc_files=[],
        created_at="2026-08-14T00:00:00Z",
    )
    state = AppState(intake_manifest=manifest)
    pipeline = SequentialQETPipeline()

    # Run complete pipeline
    state = pipeline.run(state)
    assert state.latest_report is not None
    assert "Report" in state.stage_timestamps

    # Retry Test Cases stage (resets Test Cases, Test Data, Playwright, Report)
    pipeline._reset_downstream_outputs(state, "Test Cases")

    assert state.understanding is not None
    assert state.test_suite is None
    assert state.synthetic_dataset is None
    assert state.playwright_scripts == []
    assert state.latest_report is None

    assert "Understanding" in state.stage_timestamps
    assert "Test Cases" not in state.stage_timestamps
    assert "Test Data" not in state.stage_timestamps
    assert "Playwright" not in state.stage_timestamps
    assert "Report" not in state.stage_timestamps
