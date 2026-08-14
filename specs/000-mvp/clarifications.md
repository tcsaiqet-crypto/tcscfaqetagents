# Open Clarifications & Architectural Intent — MVP Scope (000-mvp)

## Clarification Items & Resolutions

### Q1: How should CrewAI and LangChain dependencies be integrated in the MVP?
- **Resolution**: Specialist agents are defined with clean Python interfaces inheriting from `BaseAgent`. CrewAI agent definitions and LangChain structured output parsing can wrap these base classes, ensuring that the MVP is 100% demo-ready and never blocked by external framework setup or API key errors.

### Q2: How is synthetic test data distinguished from real data?
- **Resolution**: All generated datasets set `is_synthetic = True` in their schema contract. Synthetic data generators use randomized, sanitized mock formats (e.g. `synth_applicant_01@cfa-test.com`) and strictly reject real candidate PII or production payment credentials.

### Q3: What happens if a pipeline stage fails?
- **Resolution**: Stage errors are appended to `state.errors` and logged via structured logging. The pipeline halts execution immediately at the failing stage and displays an explicit error alert in Streamlit. Fabricating successful outputs upon stage failure is strictly forbidden.

### Q4: How is explicit authorization handled for Playwright execution?
- **Resolution**: In the Test Execution tab, the 'Launch Playwright UI Runner' button remains disabled until the user explicitly checks the confirmation box: "I confirm explicit authorization to run Playwright UI tests locally."
