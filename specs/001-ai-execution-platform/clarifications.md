# Clarifications — AI Execution Platform (001)

## Decisions Already Made
- AI is primary for Understanding, Test Cases, Test Data, and Playwright generation.
- Deterministic fallback remains mandatory when AI fails or produces invalid outputs.
- Execution uses an external visible browser plus live step log in the app.
- Screenshot evidence is stored under uploads/RUN-ID/artifacts/execution/YYYY/MM/.
- Evidence review uses an HTML page with PDF export.
- Best-effort app auto-start is required, but manual override remains valid for ambiguous stacks.
- Screenshots are required; video and trace capture are deferred.

## Clarified Position on Frameworks
- Current repo does not use CrewAI, LangGraph, or LangChain.
- This phase should not add CrewAI by default.
- Custom orchestration remains preferable because the pipeline is explicit, safety-sensitive, and validation-heavy.
- LangGraph is only justified later if stage orchestration becomes genuinely graph-shaped with retries, branches, or human-in-the-loop loops that exceed the current pipeline model.
- LangChain should be considered only for limited helper usage such as structured output parsing or prompt abstractions, not as the system backbone.

## Remaining Open Items
- Whether launch overrides live only in Settings or also on the Upload/Execution pages.
- Whether the evidence HTML should embed full-size images or thumbnail-first navigation.
- Whether generated Playwright scripts should be one file per case or grouped by flow.
