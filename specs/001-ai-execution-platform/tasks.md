# Task List — AI Execution Platform (001)

## T001 Truth Audit
- Identify mocked/hardcoded behavior in each agent and report surface.
- Record findings in gaps.md.

## T002 Schema Hardening
- Extend AppState and stage models with provenance, timestamps, source ids, validation status, launcher state, evidence paths.
- Add tests for schema serialization and persistence.

## T003 Pipeline Validation
- Add pre/post stage validation in pipeline orchestration.
- Fail fast on incomplete stage outputs.

## T004 Understanding AI Refactor
- Split analysis into structured sub-prompts.
- Add deterministic fallback and provenance storage.

## T005 Test Case AI Refactor
- Generate suites from Understanding outputs.
- Preserve normalization and traceability.

## T006 Test Data AI Refactor
- Generate per-test-case synthetic records.
- Enforce synthetic-only validation.

## T007 Playwright AI Refactor
- Generate page objects, tests, and fixtures from upstream outputs.
- Record selector confidence and source mappings.

## T008 Launcher Services
- Create environment detector and app launcher services.
- Add readiness checks and manual override support.

## T009 Execution Evidence
- Replace mocked step results with real subprocess execution.
- Persist step logs and screenshots.

## T010 Evidence UI
- Add in-app evidence viewer with gallery and metadata.
- Add HTML/PDF evidence export.

## T011 Report Integration
- Replace placeholder report findings with evidence-backed summaries.

## T012 Settings and Runtime Controls
- Add provider, keys, launcher override, and runtime diagnostics surfaces.

## T013 Acceptance and Hardening
- Add focused automated tests.
- Run manual end-to-end verification.
