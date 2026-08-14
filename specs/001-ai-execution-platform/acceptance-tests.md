# Acceptance Tests — AI Execution Platform (001)

| Test ID | Area | Description | Expected Result |
|---------|------|-------------|-----------------|
| AT-101 | Understanding | Run Understanding with valid ZIP and docs | AI provenance shown, structured outputs saved, fallback clearly marked if used |
| AT-102 | Test Cases | Generate cases from Understanding output | Cases linked to requirements, modules, and risk metadata |
| AT-103 | Test Data | Generate synthetic data from produced cases | Every automation candidate has mapped synthetic data |
| AT-104 | Playwright | Generate scripts from actual stage outputs | Scripts and metadata files saved, selectors carry confidence/status |
| AT-105 | Launcher | Auto-start detectable target app | App launch command, port, readiness, and logs persisted |
| AT-106 | Launcher Override | Launch unsupported app via manual override | Run proceeds using saved override without breaking safety checks |
| AT-107 | Execution | Run Playwright against launched app | External browser opens, live step logs update in app |
| AT-108 | Screenshots | Capture execution evidence | Timestamped screenshots saved in configured execution path |
| AT-109 | Evidence UI | Review evidence in app | Screenshot gallery, step details, and errors render correctly |
| AT-110 | PDF Export | Export HTML evidence page | Evidence PDF downloadable and consistent with HTML |
| AT-111 | Rerun Reset | Rerun upstream stage | Downstream artifacts invalidated and regenerated |
| AT-112 | Persistence | Refresh or restart app mid-run | Saved run resumes with consistent stage state and artifacts |
| AT-113 | Safety | Attempt production-like host | Execution blocked with clear policy error |
| AT-114 | Truthfulness | AI or launcher failure occurs | No fake success or fake evidence shown |
| AT-115 | Reports | Generate final report after execution | Summary reflects real evidence, not placeholders |

## Validation Commands
- `python -m pytest -q`
- Focused launcher, evidence, and pipeline tests per phase

## Manual End-to-End
1. Upload docs and ZIP.
2. Run Understanding.
3. Run Test Cases.
4. Run Test Data.
5. Run Playwright generation.
6. Start target app automatically or via override.
7. Execute Playwright and confirm screenshots appear.
8. Open evidence page and export PDF.
9. Rerun an upstream stage and confirm downstream reset.
