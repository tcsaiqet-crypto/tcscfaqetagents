"""Unit tests for typed Pydantic data models and contracts."""

from src.models.schemas import (
    AppState,
    ExecutionMode,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
    IntakeManifest,
    TestCase,
    TestSuite,
    SyntheticDataset,
    QualityReport,
)


def test_app_state_defaults() -> None:
    state = AppState()
    assert state.project_name == "CFA Digital Journey"
    assert state.intake_manifest is None
    assert state.playwright_scripts == []
    assert state.errors == []


def test_intake_manifest_instantiation() -> None:
    manifest = IntakeManifest(
        upload_id="upl_123",
        zip_filename="cfa_source.zip",
        extracted_path="/tmp/extracted",
        total_files=15,
        total_size_bytes=1048576,
        files=[],
        doc_files=["architecture.pdf"],
        created_at="2026-08-13T12:00:00Z"
    )
    assert manifest.upload_id == "upl_123"
    assert manifest.total_files == 15
    assert manifest.doc_files == ["architecture.pdf"]


def test_test_case_contract() -> None:
    case = TestCase(
        case_id="TC-001",
        title="Verify CFA Login with Valid Credentials",
        feature_area="Authentication",
        description="Ensure user can log in with valid credentials.",
        preconditions=["User is on login page"],
        steps=["Enter username", "Enter password", "Click Submit"],
        expected_result="User is redirected to Dashboard",
        risk_level="High",
        synthetic_data_keys=["user_login", "user_password"]
    )
    assert case.case_id == "TC-001"
    assert case.risk_level == "High"
    assert len(case.steps) == 3


def test_synthetic_dataset_contract() -> None:
    dataset = SyntheticDataset(
        dataset_id="ds_001",
        dataset_name="CFA Login Dataset",
        data_schema={"username": "string", "password": "string"},
        records=[{"username": "test_user@cfa.com", "password": "MockPassword123!"}],
        is_synthetic=True
    )
    assert dataset.is_synthetic is True
    assert len(dataset.records) == 1
    assert dataset.records[0]["username"] == "test_user@cfa.com"


def test_quality_report_contract() -> None:
    report = QualityReport(
        report_id="rep_100",
        timestamp="2026-08-13T12:00:00Z",
        total_scenarios=10,
        passed=10,
        failed=0,
        blocked=0,
        pass_rate_percentage=100.0,
        risk_assessment="Low Risk",
        failure_analyses=[]
    )
    assert report.pass_rate_percentage == 100.0
    assert report.passed == 10
