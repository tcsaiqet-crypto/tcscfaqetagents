# QET Agent Accelerator — MVP Constitution

**Version:** 1.0  
**Ratified:** 2026-08-13  
**Source of truth:** `QET_MVP_ARCHITECTURE_AND_LEAD_INSTRUCTION.md`

## 1. Mission and scope

The QET Agent Accelerator tests and reports on the **existing CFA Digital Journey**. It does not rebuild, replace, or become part of that application.

Version 1 is a one-hour demonstration vertical slice. It favors a working, understandable path from upload to report over enterprise architecture. It must not introduce microservices, FAISS or another vector database, a persistent LangGraph state machine, complex authentication, or future-feature folders.

## 2. Non-negotiable Version 1 rules

1. **Streamlit UI.** Version 1 uses Streamlit for all user interaction.
2. **ZIP-only source intake.** Application source code is accepted through one uploaded ZIP file only. Repository cloning, server filesystem paths, and URL source intake are not supported.
3. **Visible but disabled URL execution.** Application URL execution may appear in Settings or capability status, but it must not execute.
4. **Only Playwright UI execution.** Controlled Playwright UI testing is the only enabled test-execution capability. It is available only when a non-production test environment is configured and the user explicitly starts the run.
5. **Other execution disabled.** API, performance, accessibility, and security-scanner execution are disabled.
6. **Synthetic data only.** Generated test data must be unmistakably synthetic and must not be derived from real people or production records.
7. **No production use.** Production URLs, production application testing, production credentials, and real candidate information are prohibited.
8. **Untrusted archives.** Every uploaded ZIP is untrusted and must be checked before and during safe extraction. Path traversal, absolute paths, links, special files, encrypted entries, and resource-limit violations must be rejected.
9. **Structured AI output.** Agent output must conform to a declared structured contract and be validated before display, storage, or use by the next stage.
10. **Execution evidence is authoritative.** Playwright tool output and collected execution artifacts determine execution status. AI text must never change a failed or skipped tool run into a pass.
11. **Evidence and confidence.** Every AI-generated finding must identify its evidence source and confidence.
12. **Explicit execution approval.** Generated Playwright code must not run until the user reviews the generated package, confirms the target is non-production, and explicitly starts execution.
13. **Backend denial.** Disabled features must be rejected by workflow/service code even if a UI control is manipulated or a function is called directly.
14. **Visible failures.** A failed stage must show a useful error, remain failed, and stop dependent pipeline stages. The system must not fabricate successful output or silently continue.
15. **No secret leakage.** Secrets must not be committed, written into generated artifacts, shown in reports, or echoed in errors. `.env.example` contains names/placeholders only.

## 3. Minimal design principles

### 3.1 One vertical workflow

The MVP uses one Streamlit process, one simple sequential workflow service, local run folders, specialist agent modules, validated JSON contracts, and report renderers. Streamlit session state holds current demo progress; there is no database requirement.

### 3.2 Simple specialist agents

The specialist roles are:

- Application Understanding Agent
- Test Case Agent
- Synthetic Data Agent
- Playwright Generation Agent
- Quality Report Agent

CrewAI should be used for specialist definitions where practical, but the workflow must not depend on complex delegation. LangChain may be used for a model wrapper or structured parsing only when it shortens implementation. Framework configuration must not block the demo.

### 3.3 Validation before progression

A stage may consume only its declared inputs. Its structured output is validated before it is saved as successful or passed forward. Missing prerequisites, invalid output, model failure, parser failure, file failure, and tool failure are visible stage failures.

### 3.4 Minimal artifact handling

Each demo run has a generated run identifier and local folders under `uploads/`, `generated/`, and `reports/`. Filenames shown to users may be retained as sanitized metadata; storage paths are controlled by the application. JSON outputs, Playwright files, HTML, PDF, and optional execution evidence are downloadable.

### 3.5 Honest capability status

Settings must distinguish:

- enabled and available;
- enabled but not configured; and
- disabled in Version 1.

A disabled control must have no successful backend path. Playwright execution without configured test environment or explicit user approval is not available.

## 4. Required pipeline states

The workflow uses the approved sequence:

```text
IDLE
→ INTAKE_READY
→ SOURCES_UPLOADED
→ UNDERSTANDING_COMPLETE
→ TEST_CASES_COMPLETE
→ TEST_DATA_COMPLETE
→ PLAYWRIGHT_COMPLETE
→ EXECUTION_OPTIONAL
→ REPORT_COMPLETE
```

A failed stage records `FAILED` for that stage, shows the error, and leaves the last valid state unchanged. Retry starts at the failed stage after its prerequisites are still validated.

## 5. Data and evidence rules

- Uploaded business and technical documents, extracted source inventory, and selected safe text source files are analysis inputs.
- API references found in source are analysis observations only; they do not enable API execution.
- Every generated test case maps to a requirement or an explicit gap/observation where possible.
- Synthetic values use reserved/test domains and fictional identities. Real government identifiers, payment details, candidate identifiers, and credentials are prohibited.
- Every report finding includes evidence references and confidence (`high`, `medium`, or `low`).
- Execution status comes only from actual Playwright result files/stdout and is `not_run` when execution was not performed.
- Reports must not imply test execution or passed tests when scripts were generated only.

## 6. Error and safety behavior

- Errors are displayed with stage, safe summary, and recommended corrective action.
- Raw secrets, full environment values, stack traces, and unsafe filesystem paths are not shown in the UI or report.
- A pipeline run stops on the first failed required stage.
- Report generation may include an explicitly labeled `not_run` execution section; it may not invent results.
- Partially generated stage files are not presented as completed artifacts.
- Safe extraction completes into a controlled run folder or leaves no usable partial source tree.

## 7. Speckit and implementation authority

Order of authority:

1. Approved MVP architecture
2. This constitution
3. Accepted decisions in `.speckit/memory/decisions.md`
4. `specs/000-mvp/spec.md` and resolved clarifications
5. Plan, tasks, and acceptance tests
6. Implementation

A contradiction must be raised in `clarifications.md`; it must not be resolved silently. Architecture changes require Architect approval. Implementation details may be adjusted to preserve the one-hour objective if all non-negotiable rules and acceptance behavior remain intact.

## 8. Definition of MVP completion

The MVP is complete only when:

- the six task groups pass their acceptance tests;
- the upload-to-report path works with synthetic fixtures;
- unsafe ZIPs are rejected;
- structured outputs validate;
- disabled capabilities fail through direct backend calls;
- Playwright does not run without configuration and explicit approval;
- execution results, when present, come from the tool;
- report findings include evidence and confidence;
- HTML and PDF are downloadable;
- no production or real candidate data/credentials appear; and
- no enterprise or future-feature architecture has been introduced.
