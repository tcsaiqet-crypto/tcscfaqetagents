# QET Agent Accelerator — Project Constitution

## 1. Core Principles
- **Safety First**: Safe execution of code, strict zip extraction validations, zero unsafe deserialization, zero usage of `eval()`.
- **Strict Scope Boundaries**: Version 1 targets Playwright UI testing for the CFA Digital Journey application with Synthetic Data only. All other execution modes (URL execution, API testing, Performance testing, Accessibility execution, Security scanning) are strictly disabled at UI and backend engine levels.
- **Architectural Rigor**: Clean separation between UI (Streamlit), Workflow/State (LangGraph), Agents (CrewAI), Supporting Tooling (LangChain), and Core Services (Python).

## 2. Technology Stack & Framework Rules
- **UI Layer**: Streamlit for dashboard, intake, understanding, generation, execution, reporting, and settings views.
- **Orchestration Layer**: LangGraph state machine governing agent workflow steps and state transitions.
- **Specialist Agent Layer**: CrewAI for specialist agents (App Understanding, Test Case Gen, Synthetic Data Gen, Playwright Script Gen, Failure Analysis, Quality Reporting).
- **LLM & Doc Tooling**: LangChain for document processing, ZIP file understanding, and LLM chain utilities.
- **Execution & Storage**: Python 3.10+ clean services, pydantic typed contracts, structured logging.
- **Automation Engine**: Playwright Python for UI test script generation and execution with Page Object Model.

## 3. Security & Safety Governance
- **Safe ZIP Extraction**: Zip slip protection (canonical path checking), max file count limit (500 files), max total size limit (100 MB), max individual file size (10 MB), forbidden extensions list (.exe, .dll, .bat, .cmd, .sh, .ps1, .pyc, .so).
- **Controlled Execution**:
  - Uploaded source code is NEVER automatically executed.
  - Playwright scripts require explicit user confirmation before execution.
  - Disabled feature cards are blocked at both UI level and backend `ExecutionEngine`.
- **Credential & Secret Protection**: Structured logging must sanitize sensitive values; credentials must never be hardcoded.
- **No Unsafe Primitives**: `eval()`, `exec()`, `pickle.loads()`, `yaml.unsafe_load()` are strictly forbidden.

## 4. Coding & Quality Rules
- 100% Python type annotations on public signatures.
- Small, single-responsibility testable functions.
- Immutable state objects for LangGraph state passing.
- Validated JSON contracts for all AI agent outputs.
- Comprehensive unit and integration test coverage via `pytest`.
