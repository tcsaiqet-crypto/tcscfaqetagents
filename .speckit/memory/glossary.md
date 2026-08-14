# QET Agent Accelerator — MVP Glossary

| Term | MVP definition |
|---|---|
| Application URL execution | Accepting an arbitrary user-entered URL and executing tests against it. Disabled in Version 1. It is distinct from the exact non-production target configured by an operator for controlled Playwright execution. |
| Application Understanding Agent | Specialist that summarizes the uploaded application materials, discovers modules/pages/routes/UI controls/API references, validates requirement quality, identifies requirement-to-code gaps, and notes testability. |
| Artifact | A completed run file: validated JSON, generated Playwright code/data, execution evidence, HTML, or PDF. |
| CFA Digital Journey | The existing application under test. It is not implemented or rebuilt by this project. |
| Capability | A named function shown in Settings as enabled, not configured, or disabled. Backend policy is authoritative. |
| Confidence | `high`, `medium`, or `low` assessment attached to an AI finding based on the quality/directness of cited evidence. |
| Controlled Playwright execution | An explicit user-started run of generated Playwright UI tests against the exact configured non-production host. It requires configuration, code review confirmation, and non-production confirmation. |
| CrewAI | Preferred lightweight mechanism for specialist agent definitions where it does not block the demo. Complex delegation is not required. |
| Disabled capability | A visible or hidden function that backend workflow/service code refuses to execute. |
| Evidence source | A traceable document, requirement section, source file and line/locator, inventory item, generated artifact, or actual tool result supporting a finding. |
| Execution evidence | Playwright-produced results such as exit code, summary, stdout/stderr excerpt, screenshots, traces, or result files. It is authoritative for execution status. |
| Finding | A requirement gap, code gap, risk, defect observation, or recommendation with severity, evidence source, and confidence. |
| Inventory | Validated metadata for safely extracted regular files, including relative path, type/category, size, and whether selected for analysis. |
| One-hour MVP | A working demonstration vertical slice, optimized for simplicity rather than production architecture or completeness. |
| Playwright Generation Agent | Specialist that creates Python Playwright configuration, tests, a basic page object, synthetic data files, selector confidence, and review notes. |
| Production credential | Any key, token, password, cookie, certificate, connection string, or session material granting production access. Prohibited. |
| Quality Report Agent | Specialist/aggregator that turns validated stage artifacts and optional real execution results into evidence-based report data. |
| Requirement validation | Assessment of each requirement set against the approved 15-point checklist. Missing information is reported as a gap. |
| Run ID | Application-generated identifier used to keep one demo run’s uploads, generated files, and reports together. |
| Safe ZIP extraction | Validation and extraction that rejects absolute/traversal paths, links, special/encrypted entries, and configured resource-limit violations. |
| Sequential workflow | Simple service that invokes stages in approved order, validates prerequisites and outputs, updates state, and stops on failure. |
| Source inventory | List of safe extracted source files and categories; selected bounded text files become understanding inputs. |
| Structured output | Agent or service output parsed into a declared Pydantic contract before it is accepted or passed forward. |
| Synthetic data | Artificial test data that is not copied or derived from real candidate or production information and uses fictional/test-safe values. |
| Test Case Agent | Specialist that generates positive, negative, boundary, and validation cases with requirement/module mapping, priority, and automation candidacy. |
| Tool evidence is authoritative | A report can say a test passed or failed only from actual Playwright output. AI narrative cannot override or invent tool status. |
| Workflow state | One of the approved states from `IDLE` through `REPORT_COMPLETE`; a stage failure does not advance it. |
