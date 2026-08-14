# F05 UX Observability and Provenance

## Outcome
Users can see exactly what the system is doing and why, including AI provenance and actionable failure context.

## Scope
- Render processing timeline on Home.
- Render AI provenance and validation status on Understanding.
- Add error surfaces with retry actions.
- Keep non-functional tabs visible but disabled with gating hints.

## Home Observability
- Show lifecycle state chips and progress timeline.
- Show counts for uploaded docs, indexed files, and processing outcomes.
- Show most recent backend message and timestamp.

## Understanding Observability
Display:
- provider and model
- prompt version or hash
- generated timestamp
- fallback_used flag
- validation status
- concise diagnostics when failed

## Error UX
1. Distinguish retryable from non-retryable errors.
2. Preserve user context after failures.
3. Surface remediation hints instead of generic messages.

## Done Criteria
1. Operators can diagnose failures without checking server logs first.
2. AI provenance is visible and auditable.
3. State transitions and errors are understandable in one screen.
