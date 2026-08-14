# QET Agent Accelerator — Architecture Specification

## 1. System Overview
The Quality Engineering & Testing (QET) Agent Accelerator is a stateful multi-agent system designed for automated testing of the CFA Digital Journey application.

```
+-----------------------------------------------------------------------------------+
|                                  Streamlit UI                                     |
|  [Dashboard] [Intake] [App Understanding] [Test Cases] [Synthetic Data]           |
|  [Playwright Scripts] [Test Execution] [Quality Report] [Settings]                |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                             LangGraph Workflow Engine                             |
|  State: AppState (intake_data -> understanding -> test_cases -> scripts -> run)   |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                                CrewAI Specialist Agents                           |
|  - App Understanding Agent                                                        |
|  - Test Case Generation Agent                                                     |
|  - Synthetic Data Agent                                                           |
|  - Playwright Script Generation Agent                                             |
|  - Test Execution & Failure Analysis Agent                                        |
|  - Quality Reporting Agent                                                        |
+-----------------------------------------------------------------------------------+
                                         |
                                         v
+-----------------------------------------------------------------------------------+
|                           Services & Safety Layer (Python)                        |
|  - ZipService (Safe zip extraction, file tree indexing, limits)                   |
|  - ExecutionEngine (Blocks disabled cards: URL, API, Perf, A11y, Sec)             |
|  - PlaywrightRunner (Page Object Model execution, screenshots, traces)            |
|  - ReportGenerator (HTML & PDF export)                                            |
+-----------------------------------------------------------------------------------+
```

## 2. Directory & Module Boundaries
- `src/config.py`: Application settings, execution limits, environment defaults.
- `src/models/schemas.py`: Typed Pydantic schemas for state, intake artifacts, agent outputs, test cases, scripts, execution logs.
- `src/utils/security.py`: Zip extraction sanitizer, path validator, secret mask logger.
- `src/utils/logger.py`: Structured JSON/Console logging system.
- `src/services/zip_service.py`: High-level zip upload validator, parser, file analyzer.
- `src/services/execution_engine.py`: Execution guard enforcing execution mode constraints (UI testing allowed; URL/API/Perf/A11y/Sec strictly blocked).
- `src/services/report_service.py`: HTML and PDF report generator.
- `src/agents/`: CrewAI agent definitions for each specialist domain.
- `src/workflows/`: LangGraph graph definitions and state transition handlers.

## 3. Data Flow & Safe Hand-off
1. **Intake**: ZIP archive uploaded -> `ZipService` sanitizes extraction -> indices source tree & supporting documents.
2. **App Understanding**: `AppUnderstandingAgent` analyzes codebase -> produces structured architecture summary & user flow maps.
3. **Test Generation**: `TestCaseGenAgent` generates structured test suites with risk ratings -> `SyntheticDataAgent` generates synthetic data payloads.
4. **Automation**: `PlaywrightScriptAgent` generates Playwright scripts using POM & data-testid selectors.
5. **Execution**: `ExecutionEngine` checks mode permissions -> executes Playwright UI tests only upon explicit trigger -> captures screenshots & traces.
6. **Reporting**: `ReportService` formats execution results into HTML and PDF exports.
