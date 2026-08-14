"""Test Case Generation Specialist Agent — Phase 3 Implementation."""

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from schemas.contracts import AppState, TestCase, TestSuite
from src.agents.base_agent import BaseAgent
from src.services.llm_service import LLMService
from src.utils.logger import logger


class TestCaseAgent(BaseAgent):
    """Specialist agent synthesizing positive, negative, boundary, validation, and error-handling test cases."""

    __test__ = False

    def __init__(self, run_id: str = "RUN-20260813-001"):
        super().__init__(agent_name="TestCaseAgent", description="Positive & Negative Test Suite Generator")
        self.run_id = run_id
        self.artifact_dir = Path("uploads") / run_id / "artifacts"
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        self.llm = LLMService()

    def run(self, state: AppState) -> AppState:
        """Execute Phase 3 Test Case Generation and save artifacts."""
        logger.info("Executing Phase 3 Test Case Generation Agent...")

        test_cases = self._generate_test_cases(state)
        fallback_used = True
        provenance = {
            "generator": "TestCaseAgent",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "mode": "derived-fallback",
            "provider": "deterministic",
        }

        if self.llm.is_enabled():
            ai_cases = self._generate_ai_test_cases(state)
            if ai_cases:
                test_cases = ai_cases
                fallback_used = False
                provenance["mode"] = "ai-first"
                provenance["provider"] = self.llm._active_provider()

        suite = TestSuite(
            suite_id="TS-CFA-V1",
            name="CFA Digital Journey Comprehensive Test Suite",
            description="Positive, Negative, Boundary, Validation and Error-Handling scenarios mapped to CFA requirements.",
            test_cases=test_cases,
            provenance=provenance,
            validation_status="VALIDATED",
            fallback_used=fallback_used,
        )

        state.test_suite = suite

        # Save Required Artifacts
        self._save_artifacts(test_cases)

        logger.info(f"Phase 3 Test Case Generation complete. Generated {len(test_cases)} test cases.")
        return state

    def _generate_ai_test_cases(self, state: AppState) -> List[TestCase]:
        """Generate AI-first cases in strict JSON shape."""
        understanding_text = state.understanding.summary if state.understanding else "CFA Digital Journey"
        feature_areas = []
        if state.understanding and state.understanding.components:
            feature_areas = [component.name for component in state.understanding.components[:5]]
        prompt = (
            "Return strict JSON object with key 'test_cases' as an array with 10 to 14 items covering Positive, Negative, Boundary, Validation, and Error-Handling cases. "
            "Each item requires: case_id, title, case_type, feature_area, requirement_id, description, priority, risk_level, automation_candidate, preconditions, steps, expected_result, evidence_source, confidence, review_status, synthetic_data_keys. "
            "Use case_id format like TC-POS-001, TC-NEG-002, TC-BND-001, TC-VAL-001, TC-ERR-001. "
            "Return only JSON.\n"
            f"Application summary: {understanding_text}\n"
            f"Feature areas: {feature_areas}\n"
        )
        llm_text = self.llm.generate_text(prompt)
        llm_data = self.llm.parse_json_payload(llm_text)
        if not llm_data:
            return []

        raw_cases = llm_data.get("test_cases")
        if not isinstance(raw_cases, list):
            return []

        generated: List[TestCase] = []
        for item in raw_cases[:14]:
            if not isinstance(item, dict):
                continue
            try:
                case_type = str(item.get("case_type", "Validation"))
                feature_area = str(item.get("feature_area", "General"))
                requirement_id = str(item.get("requirement_id") or self._requirement_id_for_feature(feature_area))
                steps = item.get("steps") if isinstance(item.get("steps"), list) else ["Execute generated scenario steps in automation harness."]
                preconditions = item.get("preconditions") if isinstance(item.get("preconditions"), list) else []
                synthetic_data_keys = item.get("synthetic_data_keys") if isinstance(item.get("synthetic_data_keys"), list) else self._default_synthetic_keys(case_type, feature_area)
                generated.append(
                    TestCase(
                        case_id=str(item.get("case_id", f"TC-AI-{len(generated)+1:03d}")),
                        title=str(item.get("title", "AI Generated Scenario")),
                        case_type=case_type,
                        feature_area=feature_area,
                        requirement_id=requirement_id,
                        description=str(item.get("description", "Model-generated scenario.")),
                        expected_result=str(item.get("expected_result", "Expected behavior validated.")),
                        priority=str(item.get("priority", "Medium")),
                        risk_level=str(item.get("risk_level", "Medium")),
                        automation_candidate=bool(item.get("automation_candidate", True)),
                        preconditions=[str(x) for x in preconditions if str(x).strip()],
                        steps=[str(x) for x in steps if str(x).strip()],
                        evidence_source="LLM-Assisted Generation",
                        confidence=str(item.get("confidence", "Medium")),
                        review_status=str(item.get("review_status", "Requires Review")),
                        synthetic_data_keys=[str(x) for x in synthetic_data_keys if str(x).strip()],
                        provenance={"generator": "TestCaseAgent", "mode": "ai-first", "provider": self.llm._active_provider()},
                        upstream_ids=self._upstream_ids_for_feature(state, feature_area),
                        validation_status="VALIDATED",
                    )
                )
            except Exception:
                continue

        return generated

    def _generate_test_cases(self, state: Optional[AppState] = None) -> List[TestCase]:
        """Generate structured test cases from Understanding outputs instead of a fixed catalog."""
        understanding = state.understanding if state else None
        feature_sources = self._derive_feature_sources(understanding)
        case_specs = [
            ("Positive", "happy path behavior validates", True),
            ("Negative", "invalid input is rejected safely", True),
            ("Boundary", "boundary values are handled correctly", True),
            ("Validation", "required field and form validation rules are enforced", True),
            ("Error-Handling", "user-visible recovery behavior appears on failure", False),
        ]

        generated: List[TestCase] = []
        counters: Dict[str, int] = {"Positive": 0, "Negative": 0, "Boundary": 0, "Validation": 0, "Error-Handling": 0}

        for feature_index, feature in enumerate(feature_sources, start=1):
            for case_type, outcome_text, automation_candidate in case_specs:
                counters[case_type] += 1
                generated.append(
                    self._build_case(
                        understanding=understanding,
                        feature=feature,
                        feature_index=feature_index,
                        case_type=case_type,
                        ordinal=counters[case_type],
                        outcome_text=outcome_text,
                        automation_candidate=automation_candidate,
                    )
                )

        return generated

    def _derive_feature_sources(self, understanding: Any) -> List[Dict[str, Any]]:
        if understanding and understanding.components:
            features: List[Dict[str, Any]] = []
            for component in understanding.components[:3]:
                features.append(
                    {
                        "name": component.name,
                        "area": self._normalize_feature_area(component.name),
                        "selectors": list(component.selectors),
                        "description": component.description,
                        "component_id": component.component_id,
                    }
                )
            return features

        return [
            {"name": "Authentication", "area": "Authentication", "selectors": ["[data-testid='username-input']", "[data-testid='login-button']"], "description": "User authentication flow.", "component_id": "comp_auth"},
            {"name": "Applicant Information", "area": "Applicant Info", "selectors": ["[data-testid='fullname-input']", "[data-testid='ssn-input']", "[data-testid='submit-app-button']"], "description": "Applicant information capture flow.", "component_id": "comp_info"},
            {"name": "Document Upload", "area": "Document Upload", "selectors": ["[data-testid='document-upload-input']", "[data-testid='documents-table']"], "description": "Document attachment flow.", "component_id": "comp_docs"},
        ]

    def _build_case(
        self,
        understanding: Any,
        feature: Dict[str, Any],
        feature_index: int,
        case_type: str,
        ordinal: int,
        outcome_text: str,
        automation_candidate: bool,
    ) -> TestCase:
        feature_area = feature["area"]
        feature_name = feature["name"]
        selectors = feature["selectors"]
        requirement_id = self._requirement_id_for_feature(feature_area)
        case_id = f"TC-{self._case_type_prefix(case_type)}-{ordinal:03d}"
        title = f"{feature_name} {case_type} Scenario"
        preconditions = self._build_preconditions(feature_area, case_type)
        steps = self._build_steps(feature_name, feature_area, case_type, selectors)
        expected_result = f"Verify {feature_name.lower()} {outcome_text}."
        priority, risk_level = self._priority_and_risk(case_type, feature_area)
        review_status = "Requires Review" if case_type == "Error-Handling" else ("Approved" if case_type in {"Positive", "Negative"} else "Generated")
        evidence_source = feature.get("component_id", feature_name)
        upstream_ids = [feature.get("component_id", feature_name)]
        if understanding and getattr(understanding, "flows", None):
            upstream_ids.extend([flow.flow_id for flow in understanding.flows[:1]])

        return TestCase(
            case_id=case_id,
            title=title,
            case_type=case_type,
            feature_area=feature_area,
            requirement_id=requirement_id,
            description=f"Assess how {feature_name.lower()} behaves when the scenario is executed as a {case_type.lower()} check.",
            priority=priority,
            risk_level=risk_level,
            automation_candidate=automation_candidate,
            preconditions=preconditions,
            steps=steps,
            expected_result=expected_result,
            evidence_source=evidence_source,
            confidence="High" if case_type in {"Positive", "Negative"} else "Medium",
            review_status=review_status,
            synthetic_data_keys=self._default_synthetic_keys(case_type, feature_area),
            provenance={"generator": "TestCaseAgent", "mode": "derived-fallback"},
            upstream_ids=upstream_ids,
            validation_status="VALIDATED",
        )

    @staticmethod
    def _normalize_feature_area(name: str) -> str:
        lowered = name.lower()
        if "auth" in lowered or "login" in lowered:
            return "Authentication"
        if "document" in lowered or "upload" in lowered:
            return "Document Upload"
        if "status" in lowered:
            return "Application Status"
        return "Applicant Info"

    @staticmethod
    def _case_type_prefix(case_type: str) -> str:
        return {
            "Positive": "POS",
            "Negative": "NEG",
            "Boundary": "BND",
            "Validation": "VAL",
            "Error-Handling": "ERR",
        }.get(case_type, "GEN")

    @staticmethod
    def _requirement_id_for_feature(feature_area: str) -> str:
        if feature_area == "Authentication":
            return "REQ-AUTH-001"
        if feature_area == "Document Upload":
            return "REQ-DOC-003"
        if feature_area == "Application Status":
            return "REQ-STATUS-004"
        return "REQ-INFO-002"

    @staticmethod
    def _default_synthetic_keys(case_type: str, feature_area: str) -> List[str]:
        keys = ["username", "password"] if feature_area == "Authentication" else ["full_name", "ssn", "employment_status"]
        if feature_area == "Document Upload":
            keys.extend(["document_file", "document_bytes"])
        if case_type == "Boundary":
            keys.append("boundary_value")
        if case_type in {"Negative", "Validation"}:
            keys.append("invalid_input")
        return keys

    @staticmethod
    def _build_preconditions(feature_area: str, case_type: str) -> List[str]:
        if feature_area == "Authentication":
            base = ["User is on the login page"]
        elif feature_area == "Document Upload":
            base = ["User is on the document upload page"]
        elif feature_area == "Application Status":
            base = ["A prior submission exists with a trackable status"]
        else:
            base = ["User has navigated to the applicant information page"]
        if case_type == "Error-Handling":
            base.append("An error condition can be triggered safely in the test environment")
        return base

    @staticmethod
    def _build_steps(feature_name: str, feature_area: str, case_type: str, selectors: List[str]) -> List[str]:
        selector_hint = selectors[0] if selectors else "relevant control"
        if case_type == "Positive":
            return [f"Open the {feature_name} flow.", f"Interact with {selector_hint} using valid input.", "Submit and continue to the next screen."]
        if case_type == "Negative":
            return [f"Open the {feature_name} flow.", f"Use invalid input against {selector_hint}.", "Attempt submission and observe rejection behavior."]
        if case_type == "Boundary":
            return [f"Open the {feature_name} flow.", f"Provide a boundary value through {selector_hint}.", "Submit and inspect the boundary handling response."]
        if case_type == "Validation":
            return [f"Open the {feature_name} flow.", f"Leave or misfill {selector_hint}.", "Trigger validation and inspect the feedback."]
        return [f"Open the {feature_name} flow.", "Trigger a safe failure mode in the environment.", "Verify the user-facing recovery or error state."]

    @staticmethod
    def _priority_and_risk(case_type: str, feature_area: str) -> tuple[str, str]:
        if case_type == "Positive":
            return ("Critical", "High") if feature_area in {"Authentication", "Applicant Info"} else ("High", "Medium")
        if case_type == "Negative":
            return ("High", "High")
        if case_type == "Boundary":
            return ("Medium", "Low")
        if case_type == "Validation":
            return ("High", "Medium")
        return ("Medium", "Medium")

    @staticmethod
    def _upstream_ids_for_feature(state: AppState, feature_area: str) -> List[str]:
        if not state.understanding:
            return []
        matches = [component.component_id for component in state.understanding.components if feature_area.lower() in component.name.lower() or component.name.lower() in feature_area.lower()]
        if matches:
            return matches
        return [component.component_id for component in state.understanding.components[:1]]

    def _save_artifacts(self, test_cases: List[TestCase]) -> None:
        """Save test_cases.json, test_cases.csv, and traceability_matrix.json inside run folder."""

        # 1. Save test_cases.json
        json_path = self.artifact_dir / "test_cases.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump([tc.model_dump() for tc in test_cases], f, indent=2)

        # 2. Save test_cases.csv
        csv_path = self.artifact_dir / "test_cases.csv"
        fieldnames = [
            "case_id", "title", "case_type", "feature_area", "requirement_id",
            "priority", "risk_level", "automation_candidate", "review_status",
            "expected_result", "evidence_source", "confidence"
        ]
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for tc in test_cases:
                row = tc.model_dump()
                writer.writerow({k: row.get(k, "") for k in fieldnames})

        # 3. Save traceability_matrix.json
        matrix: Dict[str, Any] = {
            "requirement_to_tests": {},
            "component_to_tests": {}
        }
        for tc in test_cases:
            req_id = tc.requirement_id
            feat = tc.feature_area
            matrix["requirement_to_tests"].setdefault(req_id, []).append(tc.case_id)
            matrix["component_to_tests"].setdefault(feat, []).append(tc.case_id)

        matrix_path = self.artifact_dir / "traceability_matrix.json"
        with open(matrix_path, "w", encoding="utf-8") as f:
            json.dump(matrix, f, indent=2)

        logger.info(f"Saved Phase 3 artifacts in {self.artifact_dir}: test_cases.json, test_cases.csv, traceability_matrix.json")
