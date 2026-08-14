"""Sample Task Manager App -- a second, deliberately different runnable Flask target
for the QET agent suite. Simple in-memory todo list with happy/edge/negative cases
and a handful of intentional accessibility violations (paired with good examples).

SAFETY NOTICE: Local development server only. Do not expose beyond 127.0.0.1.
"""

import re
from datetime import date, datetime
from itertools import count

from flask import Flask, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)

MAX_TITLE_LENGTH = 50
PRIORITIES = ["Low", "Medium", "High"]

_id_counter = count(1)
tasks = [
    {"id": next(_id_counter), "title": "Write project charter", "priority": "High", "due_date": "2026-08-20", "completed": False},
    {"id": next(_id_counter), "title": "Review pull requests", "priority": "Medium", "due_date": "2026-08-16", "completed": True},
]


def _find_task(task_id: int):
    return next((t for t in tasks if t["id"] == task_id), None)


def _validate_task(title: str, priority: str, due_date: str):
    errors = []
    title = (title or "").strip()
    if not title:
        errors.append("Title is required.")
    elif len(title) > MAX_TITLE_LENGTH:
        errors.append(f"Title must be {MAX_TITLE_LENGTH} characters or fewer.")

    if priority not in PRIORITIES:
        errors.append("Priority must be Low, Medium, or High.")

    if due_date:
        try:
            if datetime.strptime(due_date, "%Y-%m-%d").date() < date.today():
                errors.append("Due date cannot be in the past.")
        except ValueError:
            errors.append("Due date must be in YYYY-MM-DD format.")

    return errors, title


@app.route("/")
def index():
    error = request.args.get("error")
    return render_template("index.html", tasks=tasks, priorities=PRIORITIES, error=error)


@app.route("/tasks", methods=["POST"])
def create_task():
    errors, title = _validate_task(request.form.get("title"), request.form.get("priority"), request.form.get("due_date"))
    if errors:
        return redirect(url_for("index", error=" ".join(errors)))
    tasks.append({
        "id": next(_id_counter),
        "title": title,
        "priority": request.form.get("priority"),
        "due_date": request.form.get("due_date") or "",
        "completed": False,
    })
    return redirect(url_for("index"))


@app.route("/tasks/<int:task_id>/complete", methods=["POST"])
def complete_task(task_id):
    task = _find_task(task_id)
    if task:
        task["completed"] = not task["completed"]
    return redirect(url_for("index"))


@app.route("/tasks/<int:task_id>/delete", methods=["POST"])
def delete_task(task_id):
    global tasks
    tasks = [t for t in tasks if t["id"] != task_id]
    return redirect(url_for("index"))


@app.route("/api/tasks", methods=["GET"])
def api_list_tasks():
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 10))
    except ValueError:
        return jsonify(error="page and page_size must be integers"), 400
    if page < 1:
        return jsonify(error="page must be >= 1"), 400
    page_size = max(1, min(page_size, 100))
    start = (page - 1) * page_size
    return jsonify(items=tasks[start:start + page_size], page=page, page_size=page_size, total=len(tasks))


@app.route("/api/tasks/<int:task_id>", methods=["GET"])
def api_get_task(task_id):
    task = _find_task(task_id)
    if not task:
        return jsonify(error="not found"), 404
    return jsonify(task)


@app.route("/api/tasks", methods=["POST"])
def api_create_task():
    payload = request.get_json(silent=True) or {}
    errors, title = _validate_task(payload.get("title"), payload.get("priority"), payload.get("due_date"))
    if errors:
        return jsonify(errors=errors), 422
    new_task = {
        "id": next(_id_counter), "title": title, "priority": payload.get("priority"),
        "due_date": payload.get("due_date") or "", "completed": False,
    }
    tasks.append(new_task)
    return jsonify(new_task), 201


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5050, debug=False)
