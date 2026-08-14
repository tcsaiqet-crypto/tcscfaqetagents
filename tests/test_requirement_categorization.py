"""Unit tests for F05 feature flag and requirement categorization integration."""

import os
import pytest
from pathlib import Path
from schemas.contracts import (
    AppState,
    ApplicationUnderstanding,
    ApplicationComponent,
    ApplicationFlow,
    RequirementType,
    TestCase
)
from src.config import config
from src.workflows.pipeline import SequentialQETPipeline
from src.agents.requirement_categorizer import RequirementCategorizer
from src.agents.test_case_agent import TestCaseAgent


def test_feature_flag_disabled_by_default():
    # Verify default state matches rollout strategy (disabled by default)
    assert config.features.enable_requirement_categorization is False
    
    pipeline = SequentialQETPipeline()
    assert "Requirement Categorization" not in pipeline.STAGES


def test_feature_flag_enabled_includes_stage(monkeypatch):
    monkeypatch.setattr(config.features, "enable_requirement_categorization", True)
    
    pipeline = SequentialQETPipeline()
    assert "Requirement Categorization" in pipeline.STAGES
    assert pipeline.STAGES.index("Requirement Categorization") == 1  # Between Understanding and Test Cases


def test_requirement_categorizer_heuristics():
    # Build sample understanding state
    und = ApplicationUnderstanding(
        summary="CFA Loan Journey Application",
        architecture_notes="React UI fronting FastAPI gateway",
        components=[
            ApplicationComponent(
                component_id="c_login",
                name="Security Access Login",
                type="UI Component",
                file_path="src/components/Login.tsx",
                description="Secure authentication form utilizing JWT tokens"
            ),
            ApplicationComponent(
                component_id="c_upload",
                name="Document upload zone",
                type="UI Component",
                file_path="src/components/Upload.tsx",
                description="Input validation file constraints check"
            )
        ],
        flows=[
            ApplicationFlow(
                flow_id="f_apply",
                name="Apply for loan happy path",
                start_point="/login",
                end_point="/dashboard",
                steps=["Log in", "Upload document", "Submit"],
                description="Standard applicant flow"
            )
        ]
    )
    
    state = AppState(understanding=und)
    categorizer = RequirementCategorizer(run_id="test_run_categorizer")
    
    # Run deterministic heuristics
    updated_state = categorizer.run(state)
    
    assert len(updated_state.understanding.requirements) > 0
    assert len(updated_state.understanding.requirement_categories) > 0
    
    # Verify keyword-based categorization
    login_req = next(r for r in updated_state.understanding.requirements if r.requirement_id == "REQ-C_LOGIN")
    assert login_req.type == RequirementType.Security
    assert login_req.category_id == "CAT-SEC"
    
    upload_req = next(r for r in updated_state.understanding.requirements if r.requirement_id == "REQ-C_UPLOAD")
    assert upload_req.type == RequirementType.DataQuality
    assert upload_req.category_id == "CAT-DQ"


def test_test_case_linkage_when_categorization_enabled(monkeypatch):
    monkeypatch.setattr(config.features, "enable_requirement_categorization", True)
    
    und = ApplicationUnderstanding(
        summary="Sample application",
        architecture_notes="N/A"
    )
    
    # Setup state with explicit requirement
    from schemas.contracts import Requirement
    mock_req = Requirement(
        requirement_id="REQ-AUTH-09",
        title="Password policy enforcement",
        description="Verify password length rules",
        type=RequirementType.Security,
        category_id="CAT-SEC",
        source_evidence="Login.tsx"
    )
    und.requirements = [mock_req]
    und.requirement_categories = RequirementCategorizer()._group_requirements_into_categories([mock_req])
    
    state = AppState(understanding=und)
    
    agent = TestCaseAgent(run_id="test_run_linkage")
    # Stub live LLM calls to use fallback test case builder
    monkeypatch.setattr(agent, "_generate_ai_test_cases", lambda s: agent._generate_test_cases(s))
    
    updated_state = agent.run(state)
    assert updated_state.test_suite is not None
    
    # Verify that the generated test cases are linked to REQ-AUTH-09
    cases = updated_state.test_suite.test_cases
    assert len(cases) > 0
    
    auth_cases = [c for c in cases if c.requirement_id == "REQ-AUTH-09"]
    assert len(auth_cases) == 5  # Positive, Negative, Boundary, Validation, Error-Handling
    for c in auth_cases:
        assert c.requirement_category_id == "CAT-SEC"
        assert c.requirement_type == "Security"
