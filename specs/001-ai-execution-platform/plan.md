# Implementation Plan — AI Execution Platform (001)

## Phase 0 — Truth Audit
- Classify every current output as real, heuristic, AI-generated, templated, or mocked.
- Confirm current stage routing, persistence, and safety behavior remain stable.

## Phase 1 — Data Contracts and Validation
- Extend schemas with provenance, validation, launcher, and evidence fields.
- Add pipeline-level post-stage validation.

## Phase 2 — Understanding Overhaul
- Replace narrow narrative-only AI with AI-first structured analysis.
- Add visible provenance on Understanding page.

## Phase 3 — Test Case Overhaul
- Replace fixed catalogs with AI-first test generation linked to Understanding outputs.

## Phase 4 — Test Data Overhaul
- Replace fixed dataset templates with generated synthetic data mapped to actual cases.

## Phase 5 — Playwright Generation Overhaul
- Generate scripts from actual upstream artifacts rather than fixed templates.

## Phase 6 — App Launcher Framework
- Detect stack, launch app, wait for readiness, record diagnostics, support override.

## Phase 7 — Real Execution and Screenshot Evidence
- Replace mocked step outcomes with real Playwright execution and timestamped screenshots.

## Phase 8 — Evidence Viewer and Report Integration
- Add HTML evidence surface, screenshot gallery, and PDF export.
- Link executive reports to real evidence.

## Phase 9 — Settings and Operator Controls
- Add runtime/admin controls for provider, keys, launch override, and diagnostics.

## Phase 10 — Hardening and Acceptance Closure
- Add integration coverage and manual end-to-end validation.

## Dependency Order
Phase 0 -> Phase 1 -> Phase 2 -> Phase 3 -> Phase 4 -> Phase 5 -> Phase 7 -> Phase 8 -> Phase 10
Phase 6 can start during late Phase 4 or early Phase 5.
Phase 9 can begin after Phase 6 runtime metadata exists.
