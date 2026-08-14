# Feature Specification — QET Agent Accelerator MVP (000-mvp)

## 1. User Journey Overview

```text
1. User opens Streamlit Dashboard (http://localhost:8501)
2. Navigates to Upload Sources tab -> Uploads CFA codebase ZIP & requirement docs
3. Safe Zip engine unpacks archive & indexes source files
4. User clicks 'Run Complete Pipeline' on Dashboard (or triggers individual stage buttons)
5. Sequential Agents execute:
   a. Application Understanding Agent extracts components, flows, and requirement-to-code gaps
   b. Test Case Agent generates Positive (happy path) & Negative (validation/boundary) test cases
   c. Synthetic Data Agent generates sanitized mock datasets
   d. Playwright Agent generates Page Object Model scripts & test files
   e. Quality Report Agent compiles metrics and builds HTML & PDF report artifacts
6. User reviews results across nav tabs, previews HTML report, and downloads PDF export
7. User tests restricted execution modes on Test Execution view -> confirms backend guard blocks unauthorized runs
```

## 2. Functional Requirements

### 2.1 UI & Navigation (MVP-001)
- Streamlit application containing 9 navigational views:
  1. Dashboard
  2. Upload Sources
  3. Application Understanding
  4. Test Cases
  5. Test Data
  6. Playwright Automation
  7. Execution Results
  8. Quality Report
  9. Settings
- Visual status cards depicting enabled vs disabled execution capabilities.

### 2.2 Intake & Source Inventory (MVP-002)
- Drag-and-drop ZIP archive uploader (Max 500 files, 100 MB uncompressed limit).
- Drag-and-drop supporting document uploader (PDF, MD, TXT).
- Zip Slip path traversal checking, file count checking, and forbidden extension blocking (`.exe`, `.dll`, `.bat`, `.cmd`, `.sh`, `.ps1`, `.pyc`, `.so`, `.dylib`).
- Source inventory indexing storing file relative paths, sizes, extensions, and content snippets.

### 2.3 Application Understanding & Test Cases (MVP-003)
- **Application Understanding Agent**:
  - *Inputs*: Uploaded requirement documents, extracted source file inventory.
  - *Outputs*: Application summary, component list with selectors, user flow steps, requirement-to-code gap observations.
- **Test Case Agent**:
  - *Inputs*: Synthesized Application Understanding model.
  - *Outputs*: Structured `TestCase` instances divided into **Positive** (happy path) and **Negative** (validation error, forbidden upload, authentication error) scenarios.

### 2.4 Synthetic Data & Playwright Generation (MVP-004)
- **Synthetic Data Agent**:
  - *Inputs*: Generated test cases.
  - *Outputs*: Sanitized JSON dataset mapping keys to mock values. Real candidate PII and production credentials strictly forbidden.
- **Playwright Agent**:
  - *Inputs*: UI component inventory, test cases, synthetic data.
  - *Outputs*: Modular Page Object file (`cfa_pages.py`) and test script (`test_cfa_journey.py`) using `data-testid` selectors. Flags uncertain locators.

### 2.5 Quality Report & PDF Export (MVP-005)
- **Quality Report Agent**:
  - *Inputs*: Understanding summary, test suite, synthetic data, Playwright metadata, execution status.
  - *Outputs*: Standalone HTML quality report (`quality_report.html`) and ReportLab PDF export (`quality_report.pdf`).

### 2.6 Execution Guard & End-to-End Validation (MVP-006)
- **Execution Guard**:
  - `ExecutionEngine` validates execution mode requests.
  - Enables `PLAYWRIGHT_UI` testing only when explicit user authorization is checked.
  - Raises `ExecutionNotAllowedError` for `URL_EXECUTION`, `API_TESTING`, `PERFORMANCE_TESTING`, `ACCESSIBILITY_EXECUTION`, and `SECURITY_SCANNING`.

## 3. Acceptance Criteria by Task Group

### MVP-001 (Streamlit Shell)
- Streamlit application renders all 9 navigation tabs cleanly without runtime errors.
- Sidebar displays visual status badges for enabled (Playwright UI) and disabled capabilities.

### MVP-002 (Upload & Inventory)
- Valid ZIP archive uploads and extracts safely into working workspace.
- Malicious ZIP files containing path traversal (`../file.py`) or forbidden extensions (`.exe`) are rejected with clear error messages.

### MVP-003 (Understanding & Test Cases)
- Sequential pipeline produces application understanding components and user flows.
- Test case suite contains both positive happy path and negative validation edge case scenarios.

### MVP-004 (Synthetic Data & Playwright)
- Synthetic dataset contains 100% mock data with zero real candidate PII.
- Playwright POM files (`cfa_pages.py` and `test_cfa_journey.py`) are created on disk and viewable in UI.

### MVP-005 (HTML & PDF Report)
- Interactive HTML report preview renders inside Quality Report tab.
- PDF report file is generated and downloadable via Streamlit download button.

### MVP-006 (Validation & Guard Enforcement)
- All 21 unit and integration pytest tests pass cleanly.
- Attempting to trigger disabled execution modes raises `ExecutionNotAllowedError`.
