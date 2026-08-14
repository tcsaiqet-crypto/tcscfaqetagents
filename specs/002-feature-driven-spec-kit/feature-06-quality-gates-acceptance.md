# F06 Quality Gates, Tests, and Acceptance

## Outcome
Feature delivery is test-backed, reproducible, and accepted only when end-to-end flow works in real usage.

## Test Gates
### Backend
- Endpoint contract tests for all v1 routes.
- State transition tests including error transitions.
- AI failure contract tests for understanding stage.

### Frontend
- Upload card behavior tests.
- Tab gating tests.
- Status polling and timeline rendering tests.
- Understanding success/failure rendering tests.

## Manual Acceptance Flow
1. Create run from Home.
2. Upload requirement docs.
3. Upload source ZIP.
4. Observe processing states to readiness.
5. Start understanding.
6. Verify either:
   - structured AI output with provenance, or
   - structured failure with diagnostics and retry.
7. Confirm Home and Understanding usable; other tabs disabled.

## Release Gate
A build is acceptable only if:
1. All automated tests pass.
2. Manual acceptance flow passes at least once on a realistic sample.
3. No fake pass signals are shown on failed AI processing.

## Implementation Evidence to Record
- Final endpoint list and sample responses.
- Screenshots of Home and Understanding states.
- Test execution summary.
- Known limitations list.
