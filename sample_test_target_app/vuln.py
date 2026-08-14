"""INTENTIONALLY VULNERABLE routes -- a local-only test fixture for the QET
security-scanning agent. Every route below deliberately reproduces a
well-known OWASP weakness so automated scanners have something real to find.

DO NOT deploy this blueprint outside 127.0.0.1. DO NOT reuse this code in
any production application.
"""

import base64
import hashlib
import pickle
import sqlite3
from pathlib import Path

from flask import Blueprint, current_app, jsonify, render_template, request, send_file, session

import db

vuln_bp = Blueprint("vuln", __name__, url_prefix="/vuln")

UPLOAD_DIR = Path(__file__).parent / "uploads"


@vuln_bp.get("/")
def vuln_index():
    return render_template("vuln_index.html")


@vuln_bp.get("/search")
def vuln_search():
    """OWASP A03:2021 Injection -- string-built SQL query. INTENTIONAL."""
    q = request.args.get("q", "")
    conn = db.get_connection()
    query = "SELECT id, full_name, ssn FROM applications WHERE full_name LIKE '%" + q + "%'"  # nosec
    try:
        rows = conn.execute(query).fetchall()
    except sqlite3.Error as exc:
        conn.close()
        return jsonify(error=str(exc)), 500
    conn.close()
    return jsonify(results=[dict(r) for r in rows])


@vuln_bp.post("/legacy-login")
def vuln_legacy_login():
    """OWASP A07 -- auth bypass via SQL string concatenation. INTENTIONAL."""
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    password_md5 = hashlib.md5(password.encode()).hexdigest()
    conn = db.get_connection()
    query = (
        "SELECT * FROM legacy_users WHERE username = '" + username +
        "' AND password_md5 = '" + password_md5 + "'"
    )  # nosec
    try:
        row = conn.execute(query).fetchone()
    except sqlite3.Error as exc:
        conn.close()
        return jsonify(error=str(exc)), 500
    conn.close()
    if row:
        return jsonify(authenticated=True, username=row["username"])
    return jsonify(authenticated=False), 401


@vuln_bp.get("/api/applications/<int:app_id>")
def vuln_get_application(app_id):
    """OWASP A01 -- broken access control / IDOR: no ownership check. INTENTIONAL."""
    row = db.get_application_any(app_id)
    if not row:
        return jsonify(error="not found"), 404
    return jsonify(row)


@vuln_bp.get("/comment")
def vuln_comment():
    """OWASP A03 -- reflected XSS via unescaped output. INTENTIONAL."""
    name = request.args.get("name", "Guest")
    html = "<html><body><h2>Welcome, " + name + "!</h2></body></html>"  # nosec
    return html


@vuln_bp.post("/deserialize")
def vuln_deserialize():
    """OWASP A08 -- insecure deserialization via pickle. INTENTIONAL."""
    encoded = request.form.get("payload", "")
    try:
        data = pickle.loads(base64.b64decode(encoded))  # nosec
    except Exception as exc:
        return jsonify(error=str(exc)), 400
    return jsonify(deserialized=str(data))


@vuln_bp.get("/download")
def vuln_download():
    """Path traversal -- unsanitized filename join. INTENTIONAL."""
    filename = request.args.get("file", "")
    target = UPLOAD_DIR / filename  # nosec
    if not target.exists() or not target.is_file():
        return jsonify(error="file not found"), 404
    return send_file(target)


@vuln_bp.post("/transfer")
def vuln_transfer():
    """CSRF -- state-changing POST with no token/origin check. INTENTIONAL."""
    amount = request.form.get("amount", "0")
    username = session.get("username", "anonymous")
    db.increment_balance(username, amount)
    return jsonify(status="transferred", amount=amount, username=username)


@vuln_bp.get("/crash")
def vuln_crash():
    """Security misconfiguration -- verbose debug error leakage. INTENTIONAL."""
    raise RuntimeError("Intentional crash to demonstrate verbose debug error leakage.")


@vuln_bp.get("/config")
def vuln_config():
    """Security misconfiguration -- sensitive config leakage. INTENTIONAL."""
    return jsonify(secret_key=current_app.config.get("SECRET_KEY"), debug=bool(current_app.debug))
