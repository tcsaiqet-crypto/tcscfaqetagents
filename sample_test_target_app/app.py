"""Sample Test Target App -- a deliberately rich, runnable Flask application used
as the target under test for the QET agent suite (Understanding, Test Case,
Test Data, Playwright generation/execution, and Reporting agents).

SAFETY NOTICE: This app intentionally contains OWASP-style vulnerabilities
under /vuln/* for security-scanning-agent practice. Run it locally only
(127.0.0.1). Never expose it on a shared network or deploy it anywhere.
"""

import os
import re
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename

import db
from api import api_bp
from vuln import vuln_bp

APP_DIR = Path(__file__).parent
UPLOAD_DIR = APP_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

EMPLOYMENT_OPTIONS = ["Employed", "Self-Employed", "Unemployed", "Retired"]
ALLOWED_UPLOAD_EXTENSIONS = {".pdf"}
FORBIDDEN_UPLOAD_EXTENSIONS = {".exe", ".sh", ".bat", ".cmd", ".ps1", ".dll"}
MAX_UPLOAD_BYTES = 5 * 1024 * 1024
SSN_PATTERN = re.compile(r"^\d{3}-\d{2}-\d{4}$")
# QET's TestDataAgent always uses this literal password for Negative/Authentication
# cases, regardless of username, so a matching login must always be rejected.
SYNTHETIC_NEGATIVE_PASSWORD = "WrongPassword999!"
SYNTHETIC_DOMAIN_PATTERN = re.compile(r"^[\w.\-]+@(example\.com|test\.cfa\.local)$")

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SAMPLE_APP_SECRET_KEY", "dev-only-not-a-real-secret")
app.register_blueprint(api_bp)
app.register_blueprint(vuln_bp)

db.init_db(seed=True)


@app.route("/")
def home():
    if "username" in session:
        return redirect(url_for("apply"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    username_value = ""
    if request.method == "POST":
        username_value = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        if not username_value or not password:
            error = "Email and password are required."
        else:
            user = db.get_user(username_value)
            if not user and SYNTHETIC_DOMAIN_PATTERN.match(username_value) and password != SYNTHETIC_NEGATIVE_PASSWORD:
                db.create_synthetic_user(username_value, password)
                user = db.get_user(username_value)
            if not user:
                error = "Invalid email or password."
            elif user["locked"]:
                error = "This account is locked after too many failed sign-in attempts."
            elif not check_password_hash(user["password_hash"], password):
                db.record_failed_login(username_value)
                error = "Invalid email or password."
            else:
                db.reset_failed_login(username_value)
                session["username"] = username_value
                return redirect(url_for("apply"))
    return render_template("login.html", error=error, username=username_value)


@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect(url_for("login"))


@app.route("/apply", methods=["GET", "POST"])
def apply():
    if "username" not in session:
        return redirect(url_for("login"))

    error = None
    success = None

    if request.method == "POST":
        form_name = request.form.get("form_name")
        if form_name == "applicant_info":
            error, success = _handle_applicant_info(request)
        elif form_name == "document_upload":
            error, success = _handle_document_upload(request)

    documents = db.list_documents(session["username"])
    return render_template(
        "apply.html",
        error=error,
        success=success,
        employment_options=EMPLOYMENT_OPTIONS,
        documents=documents,
    )


def _handle_applicant_info(req):
    full_name = (req.form.get("full_name") or "").strip()
    ssn = (req.form.get("ssn") or "").strip()
    employment_status = req.form.get("employment_status") or ""
    terms_accepted = req.form.get("terms_accepted") == "on"
    income_raw = req.form.get("monthly_income") or "3000"

    errors = []
    if not full_name or len(full_name) > 100:
        errors.append("Full name is required and must be 100 characters or fewer.")
    if not SSN_PATTERN.match(ssn):
        errors.append("SSN must match the format 999-00-0000.")
    if employment_status not in EMPLOYMENT_OPTIONS:
        errors.append("Employment status must be a recognized option.")
    if not terms_accepted:
        errors.append("You must accept the terms to continue.")

    try:
        income = float(income_raw)
    except ValueError:
        income = -1
    if income <= 0:
        errors.append("Monthly income must be greater than 0.")

    if errors:
        return " ".join(errors), None

    db.save_application(session["username"], full_name, ssn, employment_status, income, terms_accepted)
    return None, "Application submitted successfully."


def _handle_document_upload(req):
    file = req.files.get("document_file")
    if not file or file.filename == "":
        return "Please choose a file to upload.", None

    ext = Path(file.filename).suffix.lower()
    if ext in FORBIDDEN_UPLOAD_EXTENSIONS or ext not in ALLOWED_UPLOAD_EXTENSIONS:
        return f"File type '{ext or 'unknown'}' is not allowed. Only PDF files are accepted.", None

    file.stream.seek(0, os.SEEK_END)
    size = file.stream.tell()
    file.stream.seek(0)
    if size == 0:
        return "Uploaded file is empty.", None
    if size > MAX_UPLOAD_BYTES:
        return "Uploaded file exceeds the 5 MB size limit.", None

    safe_name = secure_filename(file.filename)
    dest = UPLOAD_DIR / f"{session['username']}_{safe_name}"
    file.save(dest)
    db.save_document(session["username"], safe_name)
    return None, "Document uploaded successfully."


@app.route("/accessibility-demo")
def accessibility_demo():
    return render_template("accessibility_demo.html")


@app.errorhandler(404)
def not_found(_exc):
    return jsonify(error="not found"), 404


if __name__ == "__main__":
    # Bind to localhost only -- this app hosts intentional vulnerabilities under /vuln/*.
    app.run(host="127.0.0.1", port=5000, debug=True)
