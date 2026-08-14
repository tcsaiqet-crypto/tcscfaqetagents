"""REST API blueprint for the Sample Test Target App -- happy path, edge, and negative cases."""

import re
import secrets
import time

from flask import Blueprint, jsonify, request
from werkzeug.security import check_password_hash

import db

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")

EMPLOYMENT_OPTIONS = ["Employed", "Self-Employed", "Unemployed", "Retired"]
SSN_PATTERN = re.compile(r"^\d{3}-\d{2}-\d{4}$")


@api_bp.get("/health")
def health():
    return jsonify(status="ok")


@api_bp.post("/auth/login")
def api_login():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    password = payload.get("password") or ""

    if not username or not password:
        return jsonify(error="username and password are required"), 400

    user = db.get_user(username)
    if not user or user["locked"] or not check_password_hash(user["password_hash"], password):
        return jsonify(error="invalid credentials"), 401

    token = secrets.token_hex(16)
    db.store_token(token, username)
    return jsonify(token=token, username=username), 200


def _current_api_user():
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        return None
    return db.get_username_for_token(auth[len("Bearer "):])


@api_bp.get("/applications")
def list_applications():
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 10))
    except ValueError:
        return jsonify(error="page and page_size must be integers"), 400

    if page < 1:
        return jsonify(error="page must be >= 1"), 400
    page_size = max(1, min(page_size, 100))  # clamp to a safe boundary

    username = _current_api_user()
    if not username:
        return jsonify(error="authentication required"), 401

    rows, total = db.list_applications_paginated(username, page, page_size)
    return jsonify(items=rows, page=page, page_size=page_size, total=total)


@api_bp.get("/applications/<int:app_id>")
def get_application(app_id):
    username = _current_api_user()
    if not username:
        return jsonify(error="authentication required"), 401
    row = db.get_application_owned(app_id, username)
    if not row:
        return jsonify(error="not found"), 404
    return jsonify(row)


@api_bp.post("/applications")
def create_application():
    username = _current_api_user()
    if not username:
        return jsonify(error="authentication required"), 401

    payload = request.get_json(silent=True) or {}
    full_name = (payload.get("full_name") or "").strip()
    ssn = (payload.get("ssn") or "").strip()
    employment_status = payload.get("employment_status") or ""

    errors = []
    if not full_name or len(full_name) > 100:
        errors.append("full_name invalid")
    if not SSN_PATTERN.match(ssn):
        errors.append("ssn invalid")
    if employment_status not in EMPLOYMENT_OPTIONS:
        errors.append("employment_status invalid")

    try:
        income = float(payload.get("monthly_income"))
    except (TypeError, ValueError):
        income = -1
    if income <= 0:
        errors.append("monthly_income must be > 0")

    if errors:
        return jsonify(errors=errors), 422

    new_id = db.save_application(username, full_name, ssn, employment_status, income, True)
    return jsonify(id=new_id), 201


@api_bp.get("/reports/slow")
def slow_report():
    """Performance-testing fixture: configurable, capped latency."""
    try:
        delay_ms = int(request.args.get("delay_ms", 500))
    except ValueError:
        return jsonify(error="delay_ms must be an integer"), 400
    delay_ms = max(0, min(delay_ms, 5000))
    time.sleep(delay_ms / 1000)
    return jsonify(delayed_ms=delay_ms, status="ok")


@api_bp.get("/reports/heavy")
def heavy_report():
    """Performance-testing fixture: configurable, capped CPU-bound work."""
    try:
        n = int(request.args.get("n", 20000))
    except ValueError:
        return jsonify(error="n must be an integer"), 400
    n = max(100, min(n, 200000))
    prime_count = _count_primes(n)
    return jsonify(upper_bound=n, prime_count=prime_count)


def _count_primes(n: int) -> int:
    sieve = bytearray([1]) * (n + 1)
    sieve[0] = 0
    sieve[1] = 0
    for i in range(2, int(n ** 0.5) + 1):
        if sieve[i]:
            start = i * i
            sieve[start:n + 1:i] = bytearray(len(range(start, n + 1, i)))
    return sum(sieve)
