# F02 Understanding AI Engine (AI-required, Fail-fast)

## Outcome
Understanding stage produces structured AI output with provenance. If AI is unavailable or invalid, stage fails explicitly with diagnostics.

## Scope
- Use existing understanding and llm services as base.
- Add API-path mode where generated understanding content is AI-required.
- Preserve deterministic guardrails only for validation/safety, not content replacement.

## Required Output Shape
- summary
- architecture_notes
- key_components
- discovered_flows
- inferred_gaps
- entry_points
- validation_status
- provenance

## Failure Policy
Return failed status when any of these occur:
- provider_disabled
- provider_key_missing
- model_timeout
- invalid_model_json
- schema_validation_failed

## Provenance Fields
- provider
- model
- prompt_version or prompt_hash
- generated_at
- fallback_used (must be false in this mode)
- validation_status

## Contracts Consumed
- POST /api/v1/runs/{run_id}/understanding/start
- GET /api/v1/runs/{run_id}/understanding

## Done Criteria
1. Successful run returns structured understanding plus provenance.
2. Failure returns structured diagnostics and retry guidance.
3. No deterministic replacement content for AI-required fields.
