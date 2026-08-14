# F03 FastAPI Runtime Layer (Frontend/Backend Contract)

## Outcome
A minimal, stable FastAPI layer that exposes the first-release workflow to React while reusing existing backend logic.

## Scope
- Add FastAPI app bootstrap.
- Add route modules for runs, uploads, and understanding.
- Enable CORS for local frontend development.
- Keep transport models explicit and validated.

## Endpoint Set
1. POST /api/v1/runs
2. POST /api/v1/runs/{run_id}/documents
3. POST /api/v1/runs/{run_id}/codebase
4. GET /api/v1/runs/{run_id}/status
5. POST /api/v1/runs/{run_id}/understanding/start
6. GET /api/v1/runs/{run_id}/understanding

## Error Model
Standard fields:
- error_code
- error_message
- diagnostics
- retryable

## Design Rules
1. No heavy orchestration duplication; call existing services.
2. Keep endpoint handlers thin and testable.
3. Persist important state updates before returning.
4. Do not return success when downstream processing failed.

## Done Criteria
1. All endpoints reachable and documented.
2. Invalid requests return useful errors.
3. Integration with existing services works without breaking Streamlit flow.
