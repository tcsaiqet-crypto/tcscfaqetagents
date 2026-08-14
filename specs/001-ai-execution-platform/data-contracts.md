# Data Contracts — AI Execution Platform (001)

## AppState Additions
- `stage_timestamps: Dict[str, str]`
- `stage_validation: Dict[str, str]`
- `stage_provenance: Dict[str, dict]`
- `launcher_state: dict`
- `execution_evidence_index: dict`

## Understanding Output Requirements
- Summary
- Architecture notes
- Components
- Flows
- UI inventory
- API inventory
- Gaps
- Testability observations
- Provenance metadata
- Validation status

## Test Case Output Requirements
- Requirement linkage
- Feature/module linkage
- Automation candidacy
- Upstream source ids
- Confidence
- Validation status

## Test Data Output Requirements
- Per-case record mappings
- Synthetic-only validation flag
- Schema validation status
- Upstream case ids

## Playwright Output Requirements
- Script metadata per generated file
- Linked test_case_id values
- Selector confidence and uncertainty
- Upstream source ids

## Execution Output Requirements
- Executed test_case_ids
- Step logs
- Screenshot paths
- Failure summaries
- Timestamp
- Base URL
- Launcher context

## Report Output Requirements
- Evidence-linked summary
- Artifact references
- Requirement/test/execution traceability summary
