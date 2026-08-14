"""Unit tests for Phase 6 Report Agent, HTML Generation & ReportLab PDF Export."""

import pytest
from pathlib import Path
from schemas.contracts import AppState, TestSuite, TestCase
from src.agents.report_agent import ReportAgent


def test_html_and_pdf_report_generation(tmp_path: Path) -> None:
    agent = ReportAgent(run_id="RUN-TEST-R1")
    agent.artifact_dir = tmp_path
    
    state = AppState(run_id="RUN-TEST-R1")
    state.test_suite = TestSuite(
        suite_id="TS-1",
        name="Test Suite",
        description="Desc",
        test_cases=[
            TestCase(
                case_id="TC-POS-001",
                title="Login Test",
                feature_area="Authentication",
                description="Desc",
                expected_result="Pass"
            )
        ]
    )
    
    updated = agent.run(state)
    rep = updated.latest_report
    assert rep is not None
    
    html_path = tmp_path / "quality_report.html"
    pdf_path = tmp_path / "quality_report.pdf"
    
    assert html_path.exists()
    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 1000


def test_findings_evidence_structure() -> None:
    agent = ReportAgent(run_id="RUN-TEST-R2")
    state = AppState(run_id="RUN-TEST-R2")
    findings = agent._collect_findings(state)
    
    assert len(findings) > 0
    for f in findings:
        assert "finding_id" in f
        assert "category" in f
        assert "module" in f
        assert "severity" in f
        assert "evidence_source" in f
        assert "confidence" in f
        assert "status" in f
        assert "recommendation" in f


def test_not_run_execution_truthfulness(tmp_path: Path) -> None:
    agent = ReportAgent(run_id="RUN-TEST-R3")
    agent.artifact_dir = tmp_path
    state = AppState(run_id="RUN-TEST-R3")  # No execution result attached
    
    updated = agent.run(state)
    html_text = (tmp_path / "quality_report.html").read_text(encoding="utf-8")
    
    assert "NOT_RUN / NOT_CONFIGURED" in html_text
    assert updated.latest_report.passed == 0


def test_no_secret_or_pii_leakage(tmp_path: Path) -> None:
    agent = ReportAgent(run_id="RUN-TEST-R4")
    agent.artifact_dir = tmp_path
    state = AppState(run_id="RUN-TEST-R4")
    
    agent.run(state)
    html_text = (tmp_path / "quality_report.html").read_text(encoding="utf-8")
    
    assert "secret" not in html_text.lower() or "no_secret" in html_text.lower()
    assert "password123" not in html_text.lower()
