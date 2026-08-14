# Antigravity Master Prompt (Final Spec-Kit Execution)

You are Antigravity, implementing the full feature-driven spec-kit in this repository.

## Mission
Deliver a production-grade first release of the React-first flow centered on Home plus Understanding, backed by a minimal FastAPI layer that reuses existing Python services. Keep the current Streamlit application intact and operational while adding this new track.

## Source of Truth
Use this feature kit as implementation authority:
- feature-01-home-upload-react.md
- feature-02-understanding-ai-failfast.md
- feature-03-fastapi-runtime-layer.md
- feature-04-run-state-persistence.md
- feature-05-ux-observability.md
- feature-06-quality-gates-acceptance.md

## Mandatory Rules
1. Do not delete or break existing Streamlit paths unless explicitly requested.
2. Implement the new frontend as a separate React + Vite + TypeScript project in a new folder.
3. Implement backend endpoints in FastAPI for run creation, uploads, status polling, understanding start, and understanding result retrieval.
4. Understanding content generation in this flow is AI-required.
5. If AI is unavailable, malformed, times out, or fails schema validation, mark stage failed and return diagnostics.
6. Do not generate fake success, fake evidence, or placeholder pass results.
7. Persist state changes for every step to run storage.
8. Keep all existing tests green and add focused tests for each new feature.

## Expected Deliverables
1. New React app with modern Home and Understanding pages.
2. Horizontal tab shell: Home and Understanding enabled by state gating; other tabs visible but disabled.
3. Drag-drop upload cards for documents and ZIP source code.
4. Backend processing lifecycle visualization: uploading, processing_zip, indexing, ai_understanding_running, understanding_ready, error.
5. FastAPI endpoints with stable JSON contracts.
6. AI provenance metadata in Understanding output: provider, timestamp, prompt version/hash, fallback_used false in AI-required mode, validation status.
7. Retry support for failed Understanding runs.
8. Tests and verification artifacts.

## API Contract (Minimum)
- POST /api/v1/runs
  - response: { run_id, state }
- POST /api/v1/runs/{run_id}/documents
  - multipart docs
  - response: { uploaded_count, files }
- POST /api/v1/runs/{run_id}/codebase
  - multipart zip
  - response: { intake_manifest, state }
- GET /api/v1/runs/{run_id}/status
  - response: { state, progress, error }
- POST /api/v1/runs/{run_id}/understanding/start
  - response: { status: started }
- GET /api/v1/runs/{run_id}/understanding
  - response success: { status: ready, understanding }
  - response failure: { status: failed, error_code, error_message, diagnostics }

## State Machine Requirements
Allowed states:
- idle
- uploading
- processing_zip
- indexing
- ai_understanding_running
- understanding_ready
- error

State transition principles:
1. Persist each transition.
2. Return actionable error object on failure.
3. Keep rerun and reset behavior deterministic.

## File and Parsing Policy
1. Documents: parse supported formats and chunk for AI.
2. ZIP: validate safely, extract safely, index source inventory.
3. Exclude unsafe or irrelevant directories from deep parsing.
4. Enforce size and count limits with explicit user feedback.

## Non-Functional Requirements
1. Clear and modern UI with meaningful progress indicators.
2. Mobile-safe layout and desktop-first polish.
3. Strict schema validation on API boundaries.
4. Graceful error handling with remediation hints.

## Testing Requirements
1. Add backend tests for endpoint contracts and state transitions.
2. Add frontend tests for upload flow, status rendering, and tab gating.
3. Run full test suite and ensure no regressions.
4. Provide concise implementation summary with changed files and rationale.

## Completion Checklist
1. Feature files implemented in order with dependency-aware sequencing.
2. Home plus Understanding flow works end to end.
3. AI-required failure path is explicit and test-covered.
4. Remaining tabs shown as disabled placeholders.
5. Documentation updated with run and verification instructions.

Execute now and prioritize correctness, traceability, and test-backed delivery.
