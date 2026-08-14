# Risks and Mitigations — AI Execution Platform (001)

## Major Risks
1. AI outputs may be structurally invalid.
Mitigation: strict JSON contracts, normalization, deterministic fallback, focused tests.

2. Auto-starting arbitrary ZIP apps may fail.
Mitigation: best-effort adapters, persisted diagnostics, manual override.

3. Generated selectors may not be executable.
Mitigation: selector confidence scoring, validation hooks, operator review before execution.

4. Execution evidence may become inconsistent with actual outcomes.
Mitigation: treat raw logs and screenshot capture as authoritative and forbid placeholder evidence.

5. Scope creep may push the system toward unnecessary framework adoption.
Mitigation: keep custom pipeline as default; only adopt LangGraph or LangChain selectively when concrete complexity justifies it.

## CrewAI / LangGraph / LangChain Position
- CrewAI is not required for this repo now.
- The current system is a controlled sequential pipeline with strong validation and explicit state handoff, which fits custom orchestration better than CrewAI.
- LangGraph is a future option only if orchestration becomes dynamic enough to justify graph-native control.
- LangChain is acceptable only for focused helper use, not as the main execution backbone.
