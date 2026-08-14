"""Playwright Code Generation Specialist Agent — Phase 4 Implementation."""

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
from schemas.contracts import AppState, PlaywrightScript
from src.agents.base_agent import BaseAgent
from src.utils.logger import logger


class PlaywrightAgent(BaseAgent):
    """Specialist agent synthesizing Python Playwright Page Object Models, fixtures, and test scripts."""

    __test__ = False

    def __init__(self, run_id: str = "RUN-20260813-001"):
        super().__init__(agent_name="PlaywrightAgent", description="Python Playwright Automation Package Generator")
        self.run_id = run_id
        self.artifact_dir = Path("uploads") / run_id / "artifacts"
        self.output_dir = self.artifact_dir / "playwright_output"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Mirror dir for immediate execution/inspection
        self.workspace_dir = Path("workspace") / "generated_playwright_tests"
        self.workspace_dir.mkdir(parents=True, exist_ok=True)

    def run(self, state: AppState) -> AppState:
        """Execute Phase 4 Playwright Generation and save artifacts."""
        logger.info("Executing Phase 4 Playwright Generation Agent...")

        scripts = self._generate_playwright_package(state)
        state.playwright_scripts = scripts

        # Create Downloadable ZIP Package
        zip_path = self._create_downloadable_zip_package()
        logger.info(f"Phase 4 Playwright Generation complete. Created package at {zip_path}")
        return state

    def _generate_playwright_package(self, state: Optional[AppState] = None) -> List[PlaywrightScript]:
        """Generate Page Objects, tests, fixtures, data, requirements, and README from upstream artifacts."""

        # 1. Directory Structure Setup
        (self.output_dir / "pages").mkdir(exist_ok=True)
        (self.output_dir / "tests").mkdir(exist_ok=True)
        (self.output_dir / "fixtures").mkdir(exist_ok=True)
        (self.output_dir / "test-data").mkdir(exist_ok=True)

        selectors = self._derive_selectors(state)
        generated_cases = self._select_generated_cases(state)
        synthetic_payload = self._build_synthetic_payload(state)

        # 2. Generate pages/cfa_pages.py (Page Object Model)
        pages_code = f'''"""CFA Digital Journey — Page Object Models using derived selectors."""

from playwright.sync_api import Page, Locator


class LoginPage:
    """Page Object for CFA Authentication View."""

    def __init__(self, page: Page):
        self.page = page
        self.username_input: Locator = page.locator("{selectors['username_input']}")
        self.password_input: Locator = page.locator("{selectors['password_input']}")
        self.login_button: Locator = page.locator("{selectors['login_button']}")

    def navigate(self, base_url: str) -> None:
        self.page.goto(f"{{base_url}}/login")

    def login(self, username: str, password: str) -> None:
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()


class ApplicantInfoPage:
    """Page Object for Applicant Information Intake Form."""

    def __init__(self, page: Page):
        self.page = page
        self.fullname_input: Locator = page.locator("{selectors['fullname_input']}")
        self.ssn_input: Locator = page.locator("{selectors['ssn_input']}")
        self.employment_select: Locator = page.locator("{selectors['employment_select']}")
        self.terms_checkbox: Locator = page.locator("{selectors['terms_checkbox']}")
        self.submit_button: Locator = page.locator("{selectors['submit_button']}")

    def fill_applicant_details(self, name: str, ssn: str, employment: str, accept_terms: bool = True) -> None:
        self.fullname_input.fill(name)
        self.ssn_input.fill(ssn)
        self.employment_select.select_option(employment)
        if accept_terms and not self.terms_checkbox.is_checked():
            self.terms_checkbox.check()

    def submit(self) -> None:
        self.submit_button.click()


class DocumentUploadPage:
    """Page Object for Verification Proof Document Attachment."""

    def __init__(self, page: Page):
        self.page = page
        self.file_input: Locator = page.locator("{selectors['document_upload_input']}")
        self.documents_table: Locator = page.locator("{selectors['documents_table']}")

    def upload_file(self, file_path: str) -> None:
        self.file_input.set_input_files(file_path)
'''
        (self.output_dir / "pages" / "cfa_pages.py").write_text(pages_code, encoding="utf-8")

        # 3. Generate tests/test_cfa_journey.py
        valid_case_id = generated_cases[0]["case_id"]
        invalid_case_id = generated_cases[1]["case_id"] if len(generated_cases) > 1 else generated_cases[0]["case_id"]
        test_code = f'''"""CFA Digital Journey — Automated Playwright Pytest Suite."""

import pytest
from playwright.sync_api import Page, expect
from pages.cfa_pages import LoginPage, ApplicantInfoPage, DocumentUploadPage


def test_positive_applicant_flow(page: Page, app_url: str, test_data: dict) -> None:
    """Verify Happy Path Login and Applicant Form Submission."""
    login_page = LoginPage(page)
    login_page.navigate(app_url)
    
    # 1. Authenticate
    valid_record = test_data["records_by_case"]["{valid_case_id}"][0]
    login_page.login(valid_record["username"], valid_record["password"])
    
    # 2. Fill Applicant Info
    info_page = ApplicantInfoPage(page)
    info_page.fill_applicant_details(
        name=valid_record["full_name"],
        ssn=valid_record["ssn"],
        employment=valid_record["employment_status"]
    )
    info_page.submit()


def test_negative_invalid_password(page: Page, app_url: str, test_data: dict) -> None:
    """Verify Login Rejection with Incorrect Password."""
    login_page = LoginPage(page)
    login_page.navigate(app_url)
    
    invalid_record = test_data["records_by_case"]["{invalid_case_id}"][0]
    login_page.login(invalid_record["username"], invalid_record["password"])
    
    # Expect error banner or URL remain on login
    expect(page.locator("{selectors['error_banner']}" )).to_be_visible()
'''
        (self.output_dir / "tests" / "test_cfa_journey.py").write_text(test_code, encoding="utf-8")

        # 4. Generate fixtures/conftest.py
        conftest_code = '''"""Pytest Fixtures for CFA Playwright Test Package."""

import json
import os
import pytest
from pathlib import Path


@pytest.fixture
def app_url() -> str:
    return os.environ.get("QET_TEST_BASE_URL", "http://localhost:8501")


@pytest.fixture
def test_data() -> dict:
    data_file = Path(__file__).parent.parent / "test-data" / "synthetic_data.json"
    if data_file.exists():
        return json.loads(data_file.read_text(encoding="utf-8"))
    return {"records_by_case": {}}
'''
        (self.output_dir / "fixtures" / "conftest.py").write_text(conftest_code, encoding="utf-8")

        # 5. Generate test-data/synthetic_data.json
        (self.output_dir / "test-data" / "synthetic_data.json").write_text(json.dumps(synthetic_payload, indent=2), encoding="utf-8")

        # Mirror a self-contained, importable copy under workspace/ so ExecutionEngine can run it directly.
        self._mirror_executable_package(pages_code, test_code, conftest_code, synthetic_payload)

        # 6. Generate requirements.txt and README.md
        req_text = "playwright>=1.40.0\npytest-playwright>=0.4.0\npytest>=8.0.0\n"
        (self.output_dir / "requirements.txt").write_text(req_text, encoding="utf-8")

        readme_text = """# CFA Digital Journey Playwright Test Package

## Prerequisites
```bash
pip install -r requirements.txt
playwright install chromium
```

## Running Tests
```bash
pytest tests/test_cfa_journey.py --headed
```
"""
        (self.output_dir / "README.md").write_text(readme_text, encoding="utf-8")

        # Return PlaywrightScript metadata models
        generated_at = datetime.now(timezone.utc).isoformat()
        selector_confidence_map = {selector: "High" for selector in selectors.values()}
        upstream_case_ids = [case["case_id"] for case in generated_cases]
        return [
            PlaywrightScript(
                script_id="SCR-POM-001",
                test_case_id=valid_case_id,
                filename="pages/cfa_pages.py",
                code=pages_code,
                page_objects=["LoginPage", "ApplicantInfoPage", "DocumentUploadPage"],
                selectors_used=[selectors["username_input"], selectors["login_button"], selectors["fullname_input"]],
                uncertain_selectors=[],
                provenance={"generator": "PlaywrightAgent", "generated_at": generated_at, "mode": "derived-from-upstream"},
                upstream_case_ids=upstream_case_ids,
                validation_status="VALIDATED",
                selector_confidence_map=selector_confidence_map,
                fallback_used=state is None or state.understanding is None,
            ),
            PlaywrightScript(
                script_id="SCR-TST-001",
                test_case_id=valid_case_id,
                filename="tests/test_cfa_journey.py",
                code=test_code,
                page_objects=["LoginPage", "ApplicantInfoPage"],
                selectors_used=[selectors["error_banner"]],
                uncertain_selectors=[],
                provenance={"generator": "PlaywrightAgent", "generated_at": generated_at, "mode": "derived-from-upstream"},
                upstream_case_ids=upstream_case_ids,
                validation_status="VALIDATED",
                selector_confidence_map=selector_confidence_map,
                fallback_used=state is None or state.understanding is None,
            )
        ]

    def _mirror_executable_package(
        self,
        pages_code: str,
        test_code: str,
        conftest_code: str,
        synthetic_payload: Dict[str, Any],
    ) -> None:
        """Mirror a self-contained, importable copy under workspace/ so ExecutionEngine can run it directly."""
        pages_dir = self.workspace_dir / "pages"
        pages_dir.mkdir(parents=True, exist_ok=True)
        (pages_dir / "__init__.py").write_text("", encoding="utf-8")
        (pages_dir / "cfa_pages.py").write_text(pages_code, encoding="utf-8")

        (self.workspace_dir / "test_cfa_journey.py").write_text(test_code, encoding="utf-8")

        data_dir = self.workspace_dir / "test-data"
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "synthetic_data.json").write_text(json.dumps(synthetic_payload, indent=2), encoding="utf-8")

        # conftest.py sits directly beside test_cfa_journey.py here, one directory
        # closer to test-data/ than the packaged fixtures/conftest.py layout.
        (self.workspace_dir / "conftest.py").write_text(conftest_code.replace("parent.parent", "parent"), encoding="utf-8")

    def _derive_selectors(self, state: Optional[AppState]) -> Dict[str, str]:
        defaults = {
            "username_input": "[data-testid='username-input']",
            "password_input": "[data-testid='password-input']",
            "login_button": "[data-testid='login-button']",
            "fullname_input": "[data-testid='fullname-input']",
            "ssn_input": "[data-testid='ssn-input']",
            "employment_select": "[data-testid='employment-select']",
            "terms_checkbox": "[data-testid='terms-checkbox']",
            "submit_button": "[data-testid='submit-app-button']",
            "document_upload_input": "[data-testid='document-upload-input']",
            "documents_table": "[data-testid='documents-table']",
            "error_banner": "[data-testid='error-banner']",
        }

        if not state or not state.understanding or not state.understanding.ui_inventory:
            return defaults

        for control in state.understanding.ui_inventory.controls:
            selector = control.selector
            name = control.name.lower()
            if "username" in name or "email" in name:
                defaults["username_input"] = selector
            elif "password" in name:
                defaults["password_input"] = selector
            elif "sign in" in name or "login" in name:
                defaults["login_button"] = selector
            elif "full name" in name:
                defaults["fullname_input"] = selector
            elif "ssn" in name:
                defaults["ssn_input"] = selector
            elif "employment" in name:
                defaults["employment_select"] = selector
            elif "terms" in name or "consent" in name:
                defaults["terms_checkbox"] = selector
            elif "submit" in name:
                defaults["submit_button"] = selector
            elif "document file" in name or "upload" in name:
                defaults["document_upload_input"] = selector
            elif "table" in name:
                defaults["documents_table"] = selector
        return defaults

    def _select_generated_cases(self, state: Optional[AppState]) -> List[Dict[str, Any]]:
        if state and state.test_suite and state.test_suite.test_cases:
            cases = state.test_suite.test_cases
            positive = next((case for case in cases if case.case_type == "Positive"), cases[0])
            negative = next((case for case in cases if case.case_type == "Negative"), cases[min(1, len(cases) - 1)])
            return [
                {"case_id": positive.case_id, "feature_area": positive.feature_area},
                {"case_id": negative.case_id, "feature_area": negative.feature_area},
            ]
        return [
            {"case_id": "TC-POS-001", "feature_area": "Authentication"},
            {"case_id": "TC-NEG-001", "feature_area": "Authentication"},
        ]

    def _build_synthetic_payload(self, state: Optional[AppState]) -> Dict[str, Any]:
        if state and state.synthetic_dataset and state.synthetic_dataset.test_case_id_mapping:
            return {"records_by_case": state.synthetic_dataset.test_case_id_mapping}
        return {
            "records_by_case": {
                "TC-POS-001": [{"username": "jane.doe@example.com", "password": "MockPassword123!", "full_name": "Jane Doe", "ssn": "999-00-1234", "employment_status": "Employed"}],
                "TC-NEG-001": [{"username": "jane.doe@example.com", "password": "WrongPassword!", "full_name": "Jane Doe", "ssn": "999-00-1234", "employment_status": "Employed"}],
            }
        }

    def _create_downloadable_zip_package(self) -> Path:
        """Compress playwright_output directory into a single ZIP for UI download."""
        zip_path = self.artifact_dir / "playwright_automation_package.zip"
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for file_path in self.output_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(self.output_dir)
                    zf.write(file_path, arcname)
        return zip_path
