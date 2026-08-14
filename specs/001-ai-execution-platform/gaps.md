# Gap Analysis & Truth Audit — AI Execution Platform (001)

## Validation Snapshot

- Current code health: `58 passed` on `python -m pytest -q`.
- Current pipeline status: stage timestamps, stage validation, stage provenance, launcher state, and execution evidence index are now present in `AppState`, and the pipeline performs precondition/output validation.
- Conclusion: the platform shell, staged execution flow, and persistence baseline are stable, but the core AI-first generation and real execution-evidence goals of 001 remain incomplete.

## Truth Audit Matrix

| System Surface / Stage | Current Implementation Classification | Target State for 001 Platform |
| :--- | :--- | :--- |
| **Intake / Zip Service** | **REAL**: Safe ZIP extraction, path validation, file inventory, document detection. | **REAL**: Preserve safe intake + pass manifest provenance to downstream stages. |
| **Understanding Stage** | **AI-FIRST HYBRID**: AI now drives summary, architecture, entry points, components, flows, and gaps when available, with deterministic inventories and fallbacks preserved for stability. | **AI-FIRST WITH FALLBACK**: strengthen source-grounding, richer provenance, and deeper validation while keeping deterministic fallback. |
| **Test Cases Stage** | **TEMPLATED**: Pre-defined test catalog filtered and mapped to detected requirements. | **AI-FIRST GENERATION**: Dynamic test suite generated directly from Understanding outputs with requirement traceability, risk scoring, and automation candidate flags. |
| **Test Data Stage** | **TEMPLATED**: Fixed synthetic dataset schema and records. | **AI-FIRST SYNTHETIC**: Dynamic, schema-validated synthetic records generated per test case with strict non-PII enforcement. |
| **Playwright Generation** | **TEMPLATE-DRIVEN**: Code templates instantiated with detected UI element selectors. | **AI-FIRST SCRIPT GEN**: Full Page Object Model and test script generation from upstream test cases and UI inventory with selector confidence scores. |
| **App Launch Framework** | **MOCKED / MANUAL**: Extraction performed; app auto-start detection and readiness monitoring are not yet managing live background target processes. | **REAL LAUNCHER**: Stack auto-detection (React/Node/Python), background process manager, health check polling, and manual override command support. |
| **Execution Stage** | **SIMULATED**: Execution steps and outcomes generated synthetically without launching browser. | **REAL PLAYWRIGHT SUBPROCESS**: Live external browser execution, real-time step streaming to UI, and timestamped screenshot capture under `uploads/RUN-ID/artifacts/execution/YYYY/MM/`. |
| **Reporting & Evidence** | **HYBRID**: Real PDF (ReportLab) and HTML rendering, but powered by simulated metrics without live screenshot timeline evidence. | **EVIDENCE-DRIVEN**: HTML evidence viewer with screenshot timeline, step metadata, failure details, and PDF export backed by real execution artifacts. |
| **Data Contracts & State** | **PARTIALLY HARDENED**: `AppState` now tracks `stage_timestamps`, `stage_validation`, `stage_provenance`, `launcher_state`, and `execution_evidence_index`, and the pipeline validates stage outputs. Remaining gap is that agent outputs still do not populate rich provenance/evidence data consistently. | **HARDENED CONTRACTS**: all stage outputs persist rich provenance, validation, launcher, and evidence metadata end to end. |

---

## Detailed Stage Gaps

### Understanding
- AI now drives structured understanding outputs when available, not just summary-level text.
- Remaining gap: UI/API inventories and checklist scoring still rely heavily on deterministic logic rather than richer AI-grounded extraction.
- Provenance is present on `ApplicationUnderstanding`, but the source-grounding story can be strengthened further.

### Test Cases
- Base test cases come from a static catalog template.
- Traceability metadata back to specific `ApplicationComponent` or `ApplicationFlow` IDs is incomplete.

### Test Data
- Dataset is fixed and not generated per produced test case.
- Case-to-record mappings are hardcoded rather than dynamically linked.

### Playwright Generation
- Scripts use string templates instead of AI reasoning over selectors.
- Selector confidence ratings are default "High" without validation status.

### App Launch
- Source files are extracted, but no process lifecycle management exists for running the target web server.

### Execution
- Playwright steps are simulated in memory; external browser execution and screenshot capture on host are pending Phase 7.

### Reporting
- Reports render real HTML/PDF files, but data source relies on simulated pass/fail numbers instead of actual execution evidence.

### Data Contracts
- Core schema fields now exist in `contracts.py` and pipeline validation is active.
- Remaining gap: agent implementations and execution/report services do not yet populate these contracts deeply enough for full traceability.

## Closed or Partially Closed Gaps

### Closed
- Stage-level run/rerun orchestration exists.
- Downstream reset on rerun exists.
- Run persistence baseline exists.
- AppState now includes stage metadata fields needed for later phases.

### Partially Closed
- Data contract hardening is started, but not fully realized in stage outputs.
- Reporting is real at the file-generation level, but not yet evidence-first.
- Execution writes evidence JSON, but not yet real screenshot-backed evidence.

## Remaining Priority Gaps

1. Test cases must be generated from Understanding outputs rather than a prebuilt catalog.
2. Test data must be generated from real cases with complete per-case mappings.
3. Playwright generation must derive from real upstream artifacts rather than fixed templates.
4. App launch detection and lifecycle management must become real.
5. Execution must move from simulated step outcomes to real Playwright browser runs with screenshots.
6. Reports and evidence pages must be driven by real execution artifacts rather than placeholder metrics.
