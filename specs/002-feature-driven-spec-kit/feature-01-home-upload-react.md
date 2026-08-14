# F01 Home Upload Experience (React-first)

## Outcome
A modern React Home page where users can create a run and upload both requirement documents and a codebase ZIP through clear drag-drop interactions.

## Scope
- New React + Vite + TypeScript project in a separate folder.
- Home page with two upload cards:
  - Documents upload card
  - Codebase ZIP upload card
- Top horizontal tabs with state-aware enablement.
- Progress and status indicators for upload and backend processing.

## UX Requirements
1. Two independent drop zones with file type constraints.
2. Visual states per card: idle, uploading, processing, ready, error.
3. Run creation if none exists.
4. Display current run id and intake completion indicators.
5. Clear CTA to proceed to Understanding only when intake is valid.

## Validation Rules
- Reject unsupported file types with clear message.
- Enforce max size/count limits.
- Prevent ZIP upload without run id.
- Show server validation errors without losing local UI state.

## Contracts Consumed
- POST /api/v1/runs
- POST /api/v1/runs/{run_id}/documents
- POST /api/v1/runs/{run_id}/codebase
- GET /api/v1/runs/{run_id}/status

## Done Criteria
1. User can complete upload flow from a fresh session.
2. Errors are recoverable with retry.
3. Understanding tab becomes enabled after intake success.
