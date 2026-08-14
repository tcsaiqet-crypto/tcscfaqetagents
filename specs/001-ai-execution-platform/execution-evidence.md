# Execution Evidence Contract — AI Execution Platform (001)

## Evidence Storage
Primary screenshot path format:
- `uploads/RUN-ID/artifacts/execution/YYYY/MM/timestamp_step-name.png`

## Required Captures
- page-load or initial target verification screenshot
- major workflow step screenshots
- failure-state screenshots
- final-state screenshot when run completes

## Required Metadata Per Step
- timestamp
- step number
- action description
- selector or logical target
- linked test_case_id
- pass/fail status
- screenshot path
- error details when present

## Review Surface
- In-app evidence viewer with ordered step timeline
- Standalone HTML evidence page
- PDF export from the HTML evidence surface

## Truth Rules
- If a screenshot is missing, the UI must say it is missing.
- If execution did not happen, no pseudo-evidence may be displayed.
- Failure classification may be heuristic, but raw logs and actual screenshots remain authoritative.
