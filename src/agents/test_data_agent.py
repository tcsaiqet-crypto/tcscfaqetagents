"""Synthetic Test Data Specialist Agent — Phase 4 Implementation."""

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from schemas.contracts import AppState, SyntheticDataset
from src.agents.base_agent import BaseAgent
from src.utils.logger import logger


class TestDataAgent(BaseAgent):
    """Specialist agent generating sanitized, fictional mock test datasets mapped to test cases."""

    __test__ = False

    def __init__(self, run_id: str = "RUN-20260813-001"):
        super().__init__(agent_name="TestDataAgent", description="Sanitized Synthetic Data Generator")
        self.run_id = run_id
        self.artifact_dir = Path("uploads") / run_id / "artifacts"
        self.artifact_dir.mkdir(parents=True, exist_ok=True)

    def run(self, state: AppState) -> AppState:
        """Execute Phase 4 Synthetic Data Generation and save artifacts."""
        logger.info("Executing Phase 4 Synthetic Test Data Agent...")

        dataset = self._generate_synthetic_dataset(state)
        state.synthetic_dataset = dataset

        # Save Artifacts
        self._save_artifacts(dataset)

        logger.info(f"Phase 4 Synthetic Data complete. Generated {len(dataset.records)} records across test scenarios.")
        return state

    def _generate_synthetic_dataset(self, state: Optional[AppState] = None) -> SyntheticDataset:
        """Generate fictional mock records mapped dynamically to the available test cases."""
        records: List[Dict[str, Any]] = []
        mapping: Dict[str, List[Dict[str, Any]]] = {}

        test_cases = state.test_suite.test_cases if state and state.test_suite else self._default_test_case_descriptors()
        for index, test_case in enumerate(test_cases, start=1):
            record = self._build_record(index, test_case)
            records.append(record)
            mapping.setdefault(record["target_test_case"], []).append(record)

        schema_def = {
            "record_id": "string",
            "target_test_case": "string",
            "category": "string",
            "username": "string (email format)",
            "password": "string (mock password)",
            "full_name": "string",
            "ssn": "string (format 999-XX-XXXX)",
            "monthly_income": "float",
            "employment_status": "string",
            "document_file": "string",
            "terms_accepted": "boolean",
            "is_synthetic": "boolean (fixed True)"
        }

        return SyntheticDataset(
            dataset_id="DS-CFA-V1",
            dataset_name="CFA Digital Journey Fictional Test Dataset",
            data_schema=schema_def,
            records=records,
            test_case_id_mapping=mapping,
            is_synthetic=True,
            non_pii_disclaimer="Strictly fictional synthetic data. No real PII, government IDs or secrets used.",
            provenance={
                "generator": "TestDataAgent",
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "mode": "derived-from-test-cases",
            },
            upstream_case_ids=[case.case_id if hasattr(case, "case_id") else case["case_id"] for case in test_cases],
            validation_status="VALIDATED",
            synthetic_only_validated=True,
            fallback_used=state is None or state.test_suite is None,
        )

    def _build_record(self, index: int, test_case: Any) -> Dict[str, Any]:
        case_id = test_case.case_id if hasattr(test_case, "case_id") else test_case["case_id"]
        case_type = test_case.case_type if hasattr(test_case, "case_type") else test_case.get("case_type", "Positive")
        feature_area = test_case.feature_area if hasattr(test_case, "feature_area") else test_case.get("feature_area", "Applicant Info")

        username = self._username_for_case(case_id, case_type, index)
        password = "WrongPassword999!" if case_type == "Negative" and feature_area == "Authentication" else f"MockPassword{100 + index}!"
        full_name = self._full_name_for_case(case_type, index)
        ssn = self._ssn_for_case(case_type, index)
        monthly_income = self._income_for_case(case_type, index)
        document_file = self._document_for_case(case_type, feature_area)

        return {
            "record_id": f"REC-{case_type[:3].upper()}-{index:03d}",
            "target_test_case": case_id,
            "category": f"{case_type} {feature_area}",
            "username": username,
            "password": password,
            "full_name": full_name,
            "ssn": ssn,
            "monthly_income": monthly_income,
            "employment_status": "Employed" if index % 2 else "Self-Employed",
            "document_file": document_file,
            "terms_accepted": case_type != "Validation",
            "is_synthetic": True,
        }

    @staticmethod
    def _default_test_case_descriptors() -> List[Dict[str, str]]:
        return [
            {"case_id": "TC-POS-001", "case_type": "Positive", "feature_area": "Authentication"},
            {"case_id": "TC-POS-002", "case_type": "Positive", "feature_area": "Applicant Info"},
            {"case_id": "TC-NEG-001", "case_type": "Negative", "feature_area": "Authentication"},
            {"case_id": "TC-BND-001", "case_type": "Boundary", "feature_area": "Applicant Info"},
            {"case_id": "TC-VAL-001", "case_type": "Validation", "feature_area": "Document Upload"},
        ]

    @staticmethod
    def _username_for_case(case_id: str, case_type: str, index: int) -> str:
        handle = case_id.lower().replace("-", ".")
        if case_type == "Boundary":
            return f"{handle}@test.cfa.local"
        return f"{handle}@example.com"

    @staticmethod
    def _full_name_for_case(case_type: str, index: int) -> str:
        if case_type == "Boundary":
            return "A" * 100
        if case_type == "Validation":
            return "Name <script>alert('XSS')</script>"
        if case_type == "Error-Handling":
            return "Recovery Scenario User"
        return f"Synthetic User {index}"

    @staticmethod
    def _ssn_for_case(case_type: str, index: int) -> str:
        if case_type == "Negative":
            return "123-45"
        return f"999-00-{1200 + index:04d}"

    @staticmethod
    def _income_for_case(case_type: str, index: int) -> float:
        if case_type == "Boundary":
            return 0.01
        if case_type == "Error-Handling":
            return 1000.00
        return float(3000 + index * 250)

    @staticmethod
    def _document_for_case(case_type: str, feature_area: str) -> str:
        if feature_area == "Document Upload" and case_type == "Negative":
            return "payload.exe"
        if feature_area == "Document Upload" and case_type == "Error-Handling":
            return "timeout_case.pdf"
        return "sample_paystub.pdf"

    def _save_artifacts(self, dataset: SyntheticDataset) -> None:
        """Save synthetic_test_data.json and synthetic_test_data.csv inside run folder."""

        # 1. Save JSON artifact
        json_path = self.artifact_dir / "synthetic_test_data.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(dataset.model_dump(), f, indent=2)

        # 2. Save CSV artifact
        csv_path = self.artifact_dir / "synthetic_test_data.csv"
        if dataset.records:
            fieldnames = list(dataset.records[0].keys())
            with open(csv_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(dataset.records)

        logger.info(f"Saved Phase 4 synthetic data artifacts in {self.artifact_dir}: synthetic_test_data.json, synthetic_test_data.csv")
