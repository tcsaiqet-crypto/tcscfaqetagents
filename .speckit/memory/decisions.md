# QET Agent Accelerator — MVP Decision Log

**Last updated:** 2026-08-13  
**Statuses:** `APPROVED-ARCHITECTURE`, `ACCEPTED-MVP-DEFAULT`, `OPEN`

This log makes architecture-derived and small implementation decisions explicit. `ACCEPTED-MVP-DEFAULT` choices may be changed during review if the one-hour design and constitutional behavior remain intact. Architecture decisions may not be changed without Architect approval.

## Decision index

| ID | Status | Decision |
|---|---|---|
| MVP-DEC-001 | APPROVED-ARCHITECTURE | Build the QET platform around the existing CFA Digital Journey; do not rebuild the journey. |
| MVP-DEC-002 | APPROVED-ARCHITECTURE | Use Streamlit and a simple sequential workflow service. |
| MVP-DEC-003 | APPROVED-ARCHITECTURE | Accept business/technical documents and one source-code ZIP; safely extract and inventory source. |
| MVP-DEC-004 | APPROVED-ARCHITECTURE | Use specialist QE agents; CrewAI where practical, without complex delegation or persistent LangGraph. |
| MVP-DEC-005 | APPROVED-ARCHITECTURE | Enable controlled Playwright UI execution only; disable URL/API/performance/accessibility/security execution and production testing. |
| MVP-DEC-006 | APPROVED-ARCHITECTURE | Generate synthetic data only and prohibit production credentials and real candidate data. |
| MVP-DEC-007 | APPROVED-ARCHITECTURE | Produce validated JSON, Playwright files, HTML, and PDF artifacts. |
| MVP-DEC-008 | APPROVED-ARCHITECTURE | Tool evidence is authoritative; AI findings require evidence and confidence; failures cannot be fabricated as success. |
| MVP-DEC-009 | ACCEPTED-MVP-DEFAULT | Use local run folders and Streamlit session state; do not add a database. |
| MVP-DEC-010 | ACCEPTED-MVP-DEFAULT | Use Pydantic contracts for structured output and JSON serialization. |
| MVP-DEC-011 | ACCEPTED-MVP-DEFAULT | Generate Python Playwright tests for the one-hour MVP. |
| MVP-DEC-012 | ACCEPTED-MVP-DEFAULT | Use Jinja2/inline CSS for HTML and ReportLab for PDF to avoid an external HTML-to-PDF service. |
| MVP-DEC-013 | ACCEPTED-MVP-DEFAULT | Use conservative upload/extraction limits configurable through environment variables. |
| MVP-DEC-014 | ACCEPTED-MVP-DEFAULT | A configured Playwright target is environment-owned, exact-host constrained, and never entered as an arbitrary URL in the UI. |
| MVP-DEC-015 | ACCEPTED-MVP-DEFAULT | Use a fixed 15-point requirement quality checklist defined in the MVP specification. |
| MVP-DEC-016 | OPEN | Confirm the model provider, model name, and credential environment variable before MVP-003. |
| MVP-DEC-017 | OPEN | Confirm the non-production CFA test environment and exact allowed host before enabling optional execution. |

## Detailed decisions

### MVP-DEC-001 — Existing CFA journey is the target

- **Status:** APPROVED-ARCHITECTURE
- **Decision:** The repository contains only the QET Agent Accelerator. The existing CFA Digital Journey is supplied as uploaded source/documents and, optionally, a configured test target.
- **Consequence:** No CFA application implementation, seeded replacement app, or production integration is created.

### MVP-DEC-002 — One-process Streamlit workflow

- **Status:** APPROVED-ARCHITECTURE
- **Decision:** Streamlit calls a simple sequential workflow service. State is sufficient for one demo run and may be exposed through stage buttons and a Run Pipeline button.
- **Consequence:** No microservices, message bus, database orchestration, or persistent graph engine.

### MVP-DEC-003 — Upload intake

- **Status:** APPROVED-ARCHITECTURE
- **Decision:** Users upload business/technical documents and exactly one source-code ZIP. The application validates, safely extracts, inventories, and selects bounded text source files for analysis.
- **Consequence:** No Git clone, remote repository URL, arbitrary server path, or archive execution.

### MVP-DEC-004 — Agent framework use

- **Status:** APPROVED-ARCHITECTURE
- **Decision:** Create specialist agent definitions with CrewAI where practical. The workflow invokes them sequentially and validates outputs; it does not rely on autonomous delegation.
- **Consequence:** If CrewAI integration threatens the demonstration timebox, a thin specialist adapter may call the configured model directly, but role boundaries and contracts remain. Such fallback must be reported, not hidden.

### MVP-DEC-005 — Execution capability matrix

- **Status:** APPROVED-ARCHITECTURE
- **Decision:** Playwright UI execution is the only executable test family. Arbitrary application URL execution and API, performance, accessibility, security-scanner, and production execution are disabled.
- **Consequence:** Disabled controls may render but backend handlers reject them. Generated Playwright code remains unexecuted unless the optional controlled gate succeeds.

### MVP-DEC-006 — Synthetic and non-production data

- **Status:** APPROVED-ARCHITECTURE
- **Decision:** Test data is synthetic. Real candidate data, real IDs, payment data, production credentials, and production targets are prohibited.
- **Consequence:** Prompts, validators, fixtures, generated files, and reports enforce the same rule.

### MVP-DEC-007 — Artifact set

- **Status:** APPROVED-ARCHITECTURE
- **Decision:** The workflow saves structured JSON outputs, generated Playwright package files, HTML, PDF, and optional execution evidence.
- **Consequence:** UI download actions read completed artifacts only.

### MVP-DEC-008 — Evidence and failure truth

- **Status:** APPROVED-ARCHITECTURE
- **Decision:** Actual Playwright evidence determines run results. Findings cite source evidence and confidence. Failed stages stop rather than generating placeholder success.
- **Consequence:** `not_run`, `failed`, and `passed` are distinct and reportable states.

### MVP-DEC-009 — Local transient persistence

- **Status:** ACCEPTED-MVP-DEFAULT
- **Context:** The architecture defines `uploads/`, `generated/`, and `reports/` and asks for a one-hour MVP.
- **Decision:** Use a short generated `run_id` and local folders under those roots. Streamlit session state keeps current workflow state and artifact paths. No SQLite or external storage.
- **Consequence:** Restart recovery, multi-user isolation, retention automation, and audit database are outside this MVP. Filenames and paths remain application-controlled.

### MVP-DEC-010 — Structured contracts

- **Status:** ACCEPTED-MVP-DEFAULT
- **Decision:** `schemas/contracts.py` contains Pydantic models for inventory, understanding, test cases, test data, Playwright metadata/execution results, report data, findings, and stage results.
- **Consequence:** Agent output is parsed and validated before becoming a successful stage. Validation failure is visible and stops the pipeline.

### MVP-DEC-011 — Python Playwright output

- **Status:** ACCEPTED-MVP-DEFAULT
- **Decision:** Generate Python Playwright/pytest files: a basic page object, test modules, data JSON, requirements, and a small execution configuration/readme.
- **Reason:** Matches the Python Streamlit repository and avoids a second application language for the one-hour demonstration.
- **Consequence:** Optional execution requires Python Playwright and an installed Chromium browser.

### MVP-DEC-012 — Report rendering

- **Status:** ACCEPTED-MVP-DEFAULT
- **Decision:** Render standalone HTML with Jinja2 and inline CSS/simple inline SVG or CSS bars. Create PDF from the same validated report data with ReportLab.
- **Consequence:** No browser-based PDF service, external assets, or complex chart stack. HTML and PDF must tell the same factual story.

### MVP-DEC-013 — Intake limits

- **Status:** ACCEPTED-MVP-DEFAULT
- **Decision:** Default limits are: 10 MiB per document, 25 MiB ZIP upload, 100 MiB total uncompressed content, 2,000 entries, 10 MiB per extracted file, and maximum compression ratio 100:1. Nested archives are inventoried as binary files and never recursively extracted.
- **Consequence:** Values may be lowered by safe environment configuration. Raising them requires a review of demo resource risk.

### MVP-DEC-014 — Configured test environment versus URL execution

- **Status:** ACCEPTED-MVP-DEFAULT
- **Context:** Architecture disables application URL execution but allows controlled Playwright execution when a test environment is configured.
- **Decision:** The UI accepts no arbitrary target URL. Optional execution reads `QET_TEST_BASE_URL` and `QET_ALLOWED_TEST_HOST` from environment configuration and requires an exact host match plus explicit user confirmation. The values must identify a non-production environment.
- **Consequence:** Missing/mismatched configuration yields `not_configured`; it does not block script generation or reporting.

### MVP-DEC-015 — Requirement checklist

- **Status:** ACCEPTED-MVP-DEFAULT
- **Decision:** Validate requirements against the 15 points in `specs/000-mvp/spec.md`: objective, scope, actors, preconditions, trigger, happy path, alternate flows, error flows, business rules, data fields, validation rules, dependencies, non-functional expectations, acceptance outcomes, and traceability/testability.
- **Consequence:** Every point returns status, evidence, confidence, and observation; missing content is reported as a gap, not invented.

### MVP-DEC-016 — Model provider

- **Status:** OPEN
- **Needed by:** MVP-003
- **Question:** Which provider/model and environment variable are approved for the demonstration?
- **Safe default if explicitly accepted:** An OpenAI-compatible model configured only through environment variables; no key in source, uploaded files, generated artifacts, or reports.

### MVP-DEC-017 — Test execution target

- **Status:** OPEN
- **Needed by:** Optional execution in MVP-004 and the execution branch of MVP-006.
- **Question:** What is the approved non-production base URL and exact host?
- **Fallback:** Leave execution unconfigured and report `not_run`; generation and the rest of the MVP remain valid.

## Change rule

Any choice that adds persistent infrastructure, authentication, a vector database, a microservice, arbitrary URL execution, another test-execution family, production access, or a future feature folder is an architecture change and must not be introduced through implementation convenience.
