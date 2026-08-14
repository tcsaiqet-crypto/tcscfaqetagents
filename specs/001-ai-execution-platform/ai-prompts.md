# AI Prompt Contracts — AI Execution Platform (001)

## Principles
- Prompts must request strict JSON.
- Each stage must define a versioned response schema.
- Invalid model output must be normalized or rejected before persistence.

## Understanding Prompt Family
- summary and architecture
- components and selectors
- user flows
- API references
- gap analysis
- testability observations

## Test Case Prompt Family
- requirement-linked scenario generation
- positive, negative, boundary, validation, error-handling coverage
- automation candidacy and risk rationale

## Test Data Prompt Family
- synthetic record generation per case
- malformed, boundary, and edge-case records
- schema-safe values only

## Playwright Prompt Family
- page object generation
- scenario-to-script generation
- selector mapping and uncertainty marking
- fixture and data binding generation

## Required Metadata
- prompt_version
- provider
- model
- fallback_used
- validation_status
