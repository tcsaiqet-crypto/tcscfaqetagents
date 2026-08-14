# Speckit Task List — QET Agent Accelerator MVP (000-mvp)

## Task Group MVP-001 — Streamlit Shell and Navigation
- **Task ID**: `MVP-001`
- **Purpose**: Create Streamlit UI shell, 9 navigation views, status cards, and visual badges for enabled vs disabled capabilities.
- **Dependencies**: None
- **Files**: `app.py`, `schemas/contracts.py`
- **Acceptance Criteria**: App renders all 9 tabs without errors. Sidebar displays enabled status for Playwright UI and disabled badges for URL, API, Perf, A11y, Sec.
- **Validation Command**: `python -c "import app; print('App OK')"`
- **Known Risks**: Streamlit session state initialization errors if not wrapped properly.

## Task Group MVP-002 — Upload and Source Inventory
- **Task ID**: `MVP-002`
- **Purpose**: Implement document upload, ZIP upload, size/type validation, safe extraction, and source inventory inspection.
- **Dependencies**: `MVP-001`
- **Files**: `services/zip_service.py`, `services/upload_service.py`, `services/source_inventory.py`, `utils/security.py`
- **Acceptance Criteria**: ZIP extraction validates path traversal (Zip Slip), file count, file size, and forbidden extensions.
- **Validation Command**: `python -m pytest tests/test_security.py -v`
- **Known Risks**: Unsafe zip extraction vulnerable to directory traversal if `is_safe_path` is omitted.

## Task Group MVP-003 — Understanding and Test Cases
- **Task ID**: `MVP-003`
- **Purpose**: Implement Application Understanding Agent and Test Case Agent interfaces for positive and negative scenario generation.
- **Dependencies**: `MVP-002`
- **Files**: `agents/understanding_agent.py`, `agents/test_case_agent.py`, `schemas/contracts.py`
- **Acceptance Criteria**: Understanding Agent extracts UI components and user flows. Test Case Agent generates both positive happy paths and negative validation scenarios.
- **Validation Command**: `python -m pytest tests/test_schemas.py -v`
- **Known Risks**: Ambiguous source code syntax failing pattern extraction.

## Task Group MVP-004 — Synthetic Data and Playwright Generation
- **Task ID**: `MVP-004`
- **Purpose**: Implement Synthetic Data Agent and Playwright Script Generation Agent producing Page Object Model files.
- **Dependencies**: `MVP-003`
- **Files**: `agents/test_data_agent.py`, `agents/playwright_agent.py`
- **Acceptance Criteria**: Synthetic dataset contains mock data only (no PII). Playwright script creates `cfa_pages.py` and `test_cfa_journey.py` on disk.
- **Validation Command**: `python -m pytest tests/test_pipeline.py -v`
- **Known Risks**: Playwright locators drifting if `data-testid` is missing.

## Task Group MVP-005 — HTML and PDF Report
- **Task ID**: `MVP-005`
- **Purpose**: Implement Quality Reporting Agent generating HTML dashboards and downloadable PDF reports using ReportLab.
- **Dependencies**: `MVP-004`
- **Files**: `agents/report_agent.py`, `services/report_service.py`, `services/pdf_service.py`
- **Acceptance Criteria**: HTML report renders in Streamlit iframe. PDF report is generated and downloadable via UI button.
- **Validation Command**: `python -m pytest tests/test_pipeline.py -v`
- **Known Risks**: ReportLab font or table overflow issues on complex text.

## Task Group MVP-006 — End-to-End Validation
- **Task ID**: `MVP-006`
- **Purpose**: Run complete sequential pipeline with synthetic sample documents and source code; verify execution guard policy.
- **Dependencies**: `MVP-001` through `MVP-005`
- **Files**: `workflows/pipeline.py`, `services/execution_engine.py`, `tests/test_pipeline.py`
- **Acceptance Criteria**: 21+ pytest suite tests pass cleanly. `ExecutionEngine` blocks disabled execution modes with `ExecutionNotAllowedError`.
- **Validation Command**: `python -m pytest -v`
- **Known Risks**: Uncaught exceptions when running subprocess runner without explicit approval.
