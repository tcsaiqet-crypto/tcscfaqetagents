# F04 Run State Machine and Persistence

## Outcome
Reliable lifecycle tracking for each run, persisted to storage and exposed to frontend polling.

## State Model
- idle
- uploading
- processing_zip
- indexing
- ai_understanding_running
- understanding_ready
- error

## Transition Requirements
1. Every transition is persisted.
2. Failed transitions include structured error payload.
3. Rerun behavior resets downstream state deterministically.
4. Status endpoint always reflects latest persisted state.

## Persistence Requirements
- Save state in run-level storage artifact.
- Include updated timestamp and stage timestamps.
- Include provenance pointers when available.

## Done Criteria
1. State survives process refresh and can be resumed.
2. Polling returns accurate current stage and progress.
3. Transition integrity is covered by tests.
