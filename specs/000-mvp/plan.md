# Implementation Plan — QET Agent Accelerator MVP (000-mvp)

## 1. Project Structure Layout

```text
qet_agent_app/
├── app.py                      # Main Streamlit UI shell & navigation
├── requirements.txt            # Python dependencies (streamlit, playwright, reportlab, pydantic, pytest)
├── README.md                   # Project overview & quickstart instructions
├── .env.example                # Environment variables template
├── pytest.ini                  # Pytest configuration
├── agents/
│   ├── __init__.py
│   ├── base.py                 # Abstract BaseAgent contract interface
│   ├── understanding_agent.py  # Application Understanding Specialist Agent
│   ├── test_case_agent.py      # Positive & Negative Test Case Generation Agent
│   ├── test_data_agent.py      # Synthetic Data Generation Agent
│   ├── playwright_agent.py     # Page Object Model Playwright Script Agent
│   └── report_agent.py         # HTML & PDF Quality Reporting Agent
├── services/
│   ├── __init__.py
│   ├── workflow.py             # Sequential 5-agent pipeline orchestrator
│   ├── upload_service.py       # Supporting document parser
│   ├── zip_service.py          # Safe ZIP extraction & source inventory indexer
│   ├── source_inventory.py     # Source file content inspector
│   ├── artifact_service.py     # Artifact file system writer
│   ├── report_service.py       # HTML report template renderer
│   ├── pdf_service.py          # ReportLab PDF report builder
│   └── execution_engine.py     # Feature guard & Playwright execution engine
├── schemas/
│   ├── __init__.py
│   └── contracts.py            # Typed Pydantic models (AppState, TestCase, etc.)
├── prompts/
│   └── agent_prompts.py        # System prompts & structured templates
├── reports/                    # Generated HTML & PDF report directory
├── generated/                  # Generated Playwright POM & test script directory
├── uploads/                    # Extracted codebase & document storage
└── tests/
    ├── test_execution_engine.py
    ├── test_pipeline.py
    ├── test_schemas.py
    └── test_security.py
```

## 2. Dependency Matrix
- `streamlit`: Web UI framework and component rendering.
- `playwright`: UI automation engine (Page Object Model).
- `reportlab`: PDF report document generator.
- `pydantic`: Typed data contracts and schema validation.
- `pytest`: Automated test suite runner.

## 3. Artifact Storage Strategy
- Extracted source code stored under `uploads/extracted_source/`.
- Generated Playwright scripts stored under `generated/playwright_tests/`.
- HTML quality reports stored under `reports/quality_report.html`.
- PDF quality reports stored under `reports/quality_report.pdf`.

## 4. Test Verification Plan
- Run `python -m pytest -v` to execute all unit and integration tests.
