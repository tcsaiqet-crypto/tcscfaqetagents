# Constitution — AI Execution Platform (001)

## Purpose
This spec-kit governs the completion of QET Agent Accelerator from a staged MVP into a traceable AI-first testing platform.

## Non-Negotiable Rules
1. Every pipeline stage must declare and validate its input and output contract.
2. No stage may report invented success, evidence, screenshots, or execution outcomes.
3. AI is primary for Understanding, Test Cases, Test Data, and Playwright generation, but deterministic fallback is mandatory.
4. Every AI-produced artifact must record provider, timestamp, prompt contract version, fallback status, and validation status.
5. Stage handoff must be explicit through persisted AppState fields, not implicit assumptions.
6. Rerunning a stage must invalidate and regenerate all downstream outputs.
7. Execution must remain non-production only and must preserve host-approval safeguards.
8. Playwright evidence must be timestamped and stored under uploads/RUN-ID/artifacts/execution/YYYY/MM/.
9. Reports must summarize real artifacts and evidence, not placeholders or hardcoded claims.
10. Uploaded target apps should use best-effort auto-start with manual override, not fake universal support claims.

## Architecture Direction
- Default orchestration remains repository-native pipeline orchestration.
- Do not introduce CrewAI as a default dependency in this phase.
- LangGraph may be considered later only if branching graph orchestration becomes materially more complex than the current sequential pipeline.
- LangChain may be added selectively for prompt/output parsing helpers if it reduces complexity without obscuring control flow.
- Preference order: custom pipeline first, small helper libraries second, orchestration frameworks only when clear complexity justifies them.

## Quality Gates
1. Each phase must keep automated tests green.
2. New stage outputs require focused tests before downstream consumers are expanded.
3. Execution evidence must be manually verified with at least one real run before a phase is considered complete.
4. Any remaining mocked behavior must be documented in gaps.md until removed.
