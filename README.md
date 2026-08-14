# QET Agent Accelerator — CFA Digital Journey

The Quality Engineering & Testing (QET) Agent Accelerator is a stateful multi-agent system designed for automated testing of the CFA Digital Journey application.

## Quickstart Guide

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

2. Run Streamlit UI:
   ```bash
   streamlit run app.py
   ```

3. Execute Test Suite:
   ```bash
   python -m pytest -v
   ```

## Version 1 Scope
- **Enabled**: Streamlit UI, Document & ZIP Upload, Application Understanding, Positive/Negative Test Generation, Synthetic Test Data, Playwright POM Generation, Controlled Playwright Execution, HTML & PDF Quality Reports.
- **Disabled**: Arbitrary URL execution, API testing, Performance load testing, Accessibility scanning, Security scanning.
