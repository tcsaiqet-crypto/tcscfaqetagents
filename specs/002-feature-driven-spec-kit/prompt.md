# Prompt For Antigravity

You are Antigravity. Implement the feature-driven spec-kit in this repository with strict correctness, traceability, and test-backed delivery.

## Execution Target
Implement the first release of the React-first workflow focused on Home and Understanding, backed by a minimal FastAPI layer that reuses existing Python services.

## Context
- Keep the existing Streamlit app intact and working.
- Build a new React app in a separate folder.
- Implement backend APIs needed for Home and Understanding.
- Understanding generation is AI-required in this delivery scope.

## Absolute Paths (Use Exactly)
- Backend repository root: C:/Users/AkshatSinha/Documents/avd/QET agents/QET agents
- Spec-kit folder: C:/Users/AkshatSinha/Documents/avd/QET agents/QET agents/specs/002-feature-driven-spec-kit
- New frontend project folder: C:/Users/AkshatSinha/Documents/avd/qet-react-ui

## Path Instructions
1. Read spec files only from the spec-kit folder above.
2. Implement FastAPI backend changes inside the backend repository root above.
3. Create and implement the React app inside the new frontend project folder above.
4. Do not place React project files inside the backend repository.

## Read These Files First
- specs/002-feature-driven-spec-kit/README.md
- specs/002-feature-driven-spec-kit/feature-01-home-upload-react.md
- specs/002-feature-driven-spec-kit/feature-02-understanding-ai-failfast.md
- specs/002-feature-driven-spec-kit/feature-03-fastapi-runtime-layer.md
- specs/002-feature-driven-spec-kit/feature-04-run-state-persistence.md
- specs/002-feature-driven-spec-kit/feature-05-ux-observability.md
- specs/002-feature-driven-spec-kit/feature-06-quality-gates-acceptance.md

## Required Functional Scope
1. React Home page with two upload cards:
   - requirement documents upload
   - source ZIP upload
2. Horizontal tabs:
   - Home and Understanding enabled by state
   - remaining tabs visible and disabled as placeholders
3. FastAPI endpoints:
   - POST /api/v1/runs
   - POST /api/v1/runs/{run_id}/documents
   - POST /api/v1/runs/{run_id}/codebase
   - GET /api/v1/runs/{run_id}/status
   - POST /api/v1/runs/{run_id}/understanding/start
   - GET /api/v1/runs/{run_id}/understanding
4. State machine support:
   - idle
   - uploading
   - processing_zip
   - indexing
   - ai_understanding_running
   - understanding_ready
   - error
5. Understanding output with provenance:
   - provider
   - model
   - generated timestamp
   - prompt version or hash
   - validation status
   - fallback_used (must be false in AI-required mode)

## AI Failure Policy
For AI-required Understanding generation, do not return deterministic replacement content if AI fails.
Return failed status with structured diagnostics for:
- provider_disabled
- provider_key_missing
- model_timeout
- invalid_model_json
- schema_validation_failed

## Engineering Rules
1. Reuse existing backend modules where possible.
2. Keep API handlers thin and service-oriented.
3. Persist all important transitions and error states.
4. Never return fabricated success.
5. Keep existing tests green.

## Testing Requirements
1. Add backend tests for endpoint contracts and state transitions.
2. Add frontend tests for upload flow, tab gating, and understanding states.
3. Run full test suite and report results.

## Completion Criteria
A. End-to-end works: create run, upload docs and ZIP, process, run understanding, view result.
B. On AI failure, UI shows explicit diagnostics with retry.
C. Home and Understanding are complete for first release.
D. Remaining tabs are placeholders and clearly marked.
E. Delivery includes concise change summary and file-level rationale.

Start implementation now.
