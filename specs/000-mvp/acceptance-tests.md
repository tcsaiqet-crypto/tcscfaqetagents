# Acceptance Tests — QET Agent Accelerator MVP (000-mvp)

## Test Suite Overview

| Test ID | Target Component | Description | Expected Result |
|---------|------------------|-------------|-----------------|
| `AT-001` | Streamlit Navigation | Verify navigation across all 9 views | All views render cleanly without syntax/import errors |
| `AT-002` | Zip Slip Safeguard | Upload ZIP containing `../malicious.py` | ZipService raises `SecurityError` and blocks extraction |
| `AT-003` | Extension Safeguard | Upload ZIP containing `.exe` binary | ZipService raises `SecurityError` ("Forbidden file extension") |
| `AT-004` | App Understanding | Process sample CFA Digital Journey archive | UnderstandingAgent extracts components and user flows |
| `AT-005` | Test Case Gen | Run Test Case Agent | Produces POS (happy path) and NEG (validation error) test cases |
| `AT-006` | Synthetic Test Data | Run Synthetic Data Agent | Generates mock data records with `is_synthetic = True` |
| `AT-007` | Playwright POM Gen | Run Playwright Agent | Writes `cfa_pages.py` and `test_cfa_journey.py` to disk |
| `AT-008` | Report & PDF Export | Run Quality Report Agent | Writes HTML report and PDF report; PDF is downloadable |
| `AT-009` | Disabled Mode Block | Attempt URL/API/Perf/A11y/Sec execution | ExecutionEngine raises `ExecutionNotAllowedError` |
| `AT-010` | Approval Enforcement | Attempt Playwright UI execution without approval | ExecutionEngine raises `PermissionError` |

## Automated Acceptance Test Execution Command
```powershell
python -m pytest -v
```
All automated tests must pass with 0 failures and 0 warnings.
