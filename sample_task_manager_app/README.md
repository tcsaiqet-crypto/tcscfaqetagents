# Sample Task Manager App

A second, deliberately different runnable Flask target for the QET agent suite --
a simple in-memory to-do list (not the CFA/login-style flow of `sample_test_target_app`).

## Run it

```powershell
pip install -r sample_task_manager_app/requirements.txt
python sample_task_manager_app/app.py
```

Serves at `http://127.0.0.1:5050`.

## Case inventory

### UI (`/`, `POST /tasks`)
- Happy: valid title + priority + future due date -> task added
- Edge: title at exactly 50 chars (accepted), 51+ chars (rejected)
- Negative: empty title, invalid priority, due date in the past, malformed date

### API (`/api/tasks`)
- Happy: `GET /api/tasks`, `POST /api/tasks` with valid payload (201)
- Edge: `page`/`page_size` boundaries (clamped to 100, `page < 1` -> 400)
- Negative: `GET /api/tasks/<id>` unknown id -> 404; invalid payload -> 422

## Known limitation

`PlaywrightAgent` currently generates a fixed CFA-style login/applicant flow
regardless of the uploaded app, so the auto-generated Playwright script will
not exercise this app's real routes out of the box. Understanding, Test Case,
Test Data, and the static Accessibility agent all work against it as-is.

## Intentional accessibility violations (paired with good examples)

| Violation | WCAG SC | Where |
| --- | --- | --- |
| `<input name="title">` with no label | 1.3.1 | task form |
| Every task row reuses `id="task-row"` | 4.1.1 | tasks table |
| `<div onclick>` delete action, no role/tabindex | 2.1.1 | tasks table |
| `<img>` with no `alt` | 1.1.1 | below the table |
| `outline: none` on a link | 2.4.7 | "here" link |
| Generic link text ("here") | 2.4.4 | "here" link |
| Low-contrast helper text (`#cccccc` on `#ffffff`) | 1.4.3 | below the table |

Good/passing examples are also present: a skip link (2.4.1), `<html lang="en">`
(3.1.1), a non-empty `<title>` (2.4.2), and properly labeled priority/due-date
fields (1.3.1/3.3.2).
