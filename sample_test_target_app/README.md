# Sample Test Target App

A small, **runnable** Flask application built specifically to exercise every agent in this
repository's QET agent suite (Understanding, Test Case, Test Data, Playwright
generation/execution, and Reporting) against a real, live target -- instead of only a
static source snapshot.

It intentionally packs in happy-path flows, edge/boundary cases, negative/wrong cases, a
JSON REST API, OWASP-style vulnerabilities, accessibility issues, and performance-testing
endpoints, all in one place.

## Safety notice

This app contains **intentionally vulnerable** routes under `/vuln/*` (SQL injection, XSS,
insecure deserialization, IDOR, path traversal, CSRF, verbose debug errors). They exist
only so the security-scanning parts of the agent suite have real weaknesses to find.

- Run this app **locally only** (it binds to `127.0.0.1`, not `0.0.0.0`).
- Never expose it on a shared network, container, or public URL.
- Never copy the `/vuln/*` code into a real application.

## Run it

```powershell
pip install -r sample_test_target_app/requirements.txt
python sample_test_target_app/app.py
```

The app starts at `http://127.0.0.1:5000` and seeds its own SQLite database
(`test_target.db`) on first run.

When pointing the ExecutionEngine / Playwright agent at this app, set:

```powershell
$env:QET_TEST_BASE_URL = "http://127.0.0.1:5000"
$env:QET_ALLOWED_TEST_HOST = "127.0.0.1"
```

(The engine's default `QET_TEST_BASE_URL` is `http://localhost:8501`, which is the
Streamlit orchestrator itself -- not this target app.)

## Seeded accounts

| Username | Password | Purpose |
| --- | --- | --- |
| `jane.doe@example.com` | `MockPassword123!` | Happy path. Matches `PlaywrightAgent`'s default synthetic payload, so the already-generated login/applicant tests pass against this app out of the box. |
| `locked.user@example.com` | `LockedUser123!` | Edge case: account is pre-locked. |
| `admin@example.com` | `AdminPass123!` | Secondary owner, used for IDOR/ownership tests. |
| `legacy.user@example.com` | `LegacyPass123!` | Only valid against the intentionally insecure `/vuln/legacy-login`. |

## Feature / case inventory

### UI flow (`/login`, `/apply`)

Selectors match exactly what `PlaywrightAgent` (`src/agents/playwright_agent.py`) already
generates by default, so existing generated Page Objects work unmodified:
`username-input`, `password-input`, `login-button`, `fullname-input`, `ssn-input`,
`employment-select`, `terms-checkbox`, `submit-app-button`, `document-upload-input`,
`documents-table`, `error-banner`.

| Case type | Example |
| --- | --- |
| Happy path | Valid login, valid applicant info, valid PDF upload |
| Negative | Wrong password, invalid SSN format (`123-45`), terms not accepted |
| Boundary | Full name at exactly 100 chars, income at `0.01`, locked account after 5 failed logins |
| Edge (upload) | Empty file, oversized file (>5 MB), forbidden extension (`.exe`, `.sh`, `.bat`) |

### REST API (`/api/v1/*`)

- `GET /api/v1/health` -- liveness check
- `POST /api/v1/auth/login` -- happy/negative (400 missing fields, 401 bad credentials)
- `GET /api/v1/applications` -- pagination happy/edge (`page < 1` -> 400, `page_size` clamped to 100)
- `GET /api/v1/applications/<id>` -- happy/negative (404 not found, ownership-scoped)
- `POST /api/v1/applications` -- happy/negative (422 with field-level validation errors)
- `GET /api/v1/reports/slow?delay_ms=` -- performance testing (capped at 5s)
- `GET /api/v1/reports/heavy?n=` -- performance testing, CPU-bound prime count (capped at 200000)

### Intentional OWASP-style vulnerabilities (`/vuln/*`, see `/vuln/` for the full index)

`SQL Injection (A03)`, `auth bypass via injection (A07)`, `broken access control / IDOR (A01)`,
`reflected XSS (A03)`, `insecure deserialization (A08)`, `path traversal`, `CSRF`, and
`security misconfiguration (A05)` via verbose debug errors and a config-leak endpoint.

### Accessibility demo (`/accessibility-demo`)

Side-by-side bad/good examples: missing `alt` text, non-semantic clickable `div`,
low-contrast text, unlabeled input, removed focus outline -- each paired with a compliant
equivalent.

### Performance

`/api/v1/reports/slow` and `/api/v1/reports/heavy` for latency/load-style checks; the
`applications` table is seeded with 200 rows to make pagination endpoints non-trivial.
