# QET Agent Accelerator — Feature Specification (V1)

## 1. Feature Core Matrix

| Component | V1 Target Behavior | V1 Execution Status |
|-----------|--------------------|---------------------|
| ZIP Source Upload | Unpack & index code for CFA Digital Journey | ENABLED (Max 500 files, 100MB) |
| Supporting Documents | Parse text/markdown/pdf/doc context | ENABLED |
| Application Understanding | Synthesize application components & flows | ENABLED |
| Test Case Generation | Generate functional UI test scenarios | ENABLED |
| Synthetic Test Data | Generate realistic mock test data | ENABLED (Synthetic data only) |
| Playwright Script Gen | Generate Page Object Model Playwright scripts | ENABLED |
| Playwright UI Execution | Execute local UI test suites with POM | ENABLED (Requires explicit trigger) |
| HTML & PDF Reports | Export test execution summaries | ENABLED |
| Direct URL Execution | Execute against target live URLs | DISABLED |
| API Testing | Execute API endpoints & integration tests | DISABLED |
| Performance Testing | Load/stress testing against backend | DISABLED |
| Accessibility Scan | Automated WCAG/axe audits | DISABLED |
| Security Scanning | DAST/SAST security vulnerability scan | DISABLED |

## 2. Interface Requirements
The Streamlit UI must contain 9 distinct navigational views:
1. **Project Dashboard**: Executive summary, execution stats, system health, execution mode toggles (showing disabled modes as inactive cards).
2. **Intake & Sources**: Drag-and-drop ZIP archive uploader, file inspector, limit enforcement warnings.
3. **Application Understanding**: Visual flow diagrams, entry points, component hierarchy, data dependencies.
4. **Test Cases**: Searchable grid of generated test cases, severity tags, filter by feature area.
5. **Synthetic Test Data**: Mock data manager, JSON schema generator, sanitized dataset preview.
6. **Playwright Automation**: Code viewer for POM scripts, selector stability inspector, data-testid warnings.
7. **Test Execution**: Runner control panel, log stream, live execution status, explicit approval confirmation.
8. **Quality Report**: HTML preview, PDF download button, defect breakdown, execution evidence attachments.
9. **Settings**: LLM configuration, timeout settings, safe extraction path, execution policies.
