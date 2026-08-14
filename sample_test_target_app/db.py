"""SQLite persistence layer for the Sample Test Target App (local test fixture only)."""

import hashlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from werkzeug.security import generate_password_hash

DB_PATH = Path(__file__).parent / "test_target.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(seed: bool = True) -> None:
    conn = get_connection()
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            failed_attempts INTEGER NOT NULL DEFAULT 0,
            locked INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS legacy_users (
            username TEXT PRIMARY KEY,
            password_md5 TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_username TEXT NOT NULL,
            full_name TEXT NOT NULL,
            ssn TEXT NOT NULL,
            employment_status TEXT NOT NULL,
            monthly_income REAL NOT NULL,
            terms_accepted INTEGER NOT NULL,
            created_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_username TEXT NOT NULL,
            filename TEXT NOT NULL,
            uploaded_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS api_tokens (
            token TEXT PRIMARY KEY,
            username TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS balances (
            username TEXT PRIMARY KEY,
            balance REAL NOT NULL DEFAULT 0
        );
        """
    )
    conn.commit()

    if seed:
        _seed_data(conn)
    conn.close()


def _seed_data(conn: sqlite3.Connection) -> None:
    if conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()["c"] > 0:
        return  # already seeded

    seeded_users = [
        # jane.doe / MockPassword123! matches PlaywrightAgent's default synthetic
        # payload so generated happy-path/negative tests work out of the box.
        ("jane.doe@example.com", "MockPassword123!", 0, 0),
        ("locked.user@example.com", "LockedUser123!", 5, 1),
        ("admin@example.com", "AdminPass123!", 0, 0),
    ]
    for username, password, failed_attempts, locked in seeded_users:
        conn.execute(
            "INSERT INTO users (username, password_hash, failed_attempts, locked) VALUES (?, ?, ?, ?)",
            (username, generate_password_hash(password), failed_attempts, locked),
        )
        conn.execute("INSERT INTO balances (username, balance) VALUES (?, 0)", (username,))

    # Intentionally weak legacy store used only by the /vuln SQL-injection fixture.
    conn.execute(
        "INSERT INTO legacy_users (username, password_md5) VALUES (?, ?)",
        ("legacy.user@example.com", hashlib.md5(b"LegacyPass123!").hexdigest()),
    )

    now = datetime.now(timezone.utc).isoformat()
    for i in range(1, 201):
        conn.execute(
            """INSERT INTO applications
               (owner_username, full_name, ssn, employment_status, monthly_income, terms_accepted, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                "jane.doe@example.com" if i % 2 else "admin@example.com",
                f"Synthetic Applicant {i}",
                f"999-00-{1000 + i:04d}",
                "Employed" if i % 3 else "Self-Employed",
                float(2000 + i * 10),
                1,
                now,
            ),
        )
    conn.commit()


def get_user(username: str):
    conn = get_connection()
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    conn.close()
    return row


def create_synthetic_user(username: str, password: str) -> None:
    """Lazily provision a test account for QET-generated synthetic credentials.

    TestDataAgent invents a fresh username per generated test case on every
    pipeline run, so this app auto-provisions accounts under the reserved
    synthetic domains on first login instead of requiring pre-seeded users.
    """
    conn = get_connection()
    conn.execute(
        "INSERT OR IGNORE INTO users (username, password_hash, failed_attempts, locked) VALUES (?, ?, 0, 0)",
        (username, generate_password_hash(password)),
    )
    conn.execute("INSERT OR IGNORE INTO balances (username, balance) VALUES (?, 0)", (username,))
    conn.commit()
    conn.close()


def record_failed_login(username: str) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE users SET failed_attempts = failed_attempts + 1, "
        "locked = CASE WHEN failed_attempts + 1 >= 5 THEN 1 ELSE locked END WHERE username = ?",
        (username,),
    )
    conn.commit()
    conn.close()


def reset_failed_login(username: str) -> None:
    conn = get_connection()
    conn.execute("UPDATE users SET failed_attempts = 0 WHERE username = ?", (username,))
    conn.commit()
    conn.close()


def save_application(owner_username, full_name, ssn, employment_status, income, terms_accepted) -> int:
    conn = get_connection()
    cur = conn.execute(
        """INSERT INTO applications
           (owner_username, full_name, ssn, employment_status, monthly_income, terms_accepted, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (
            owner_username, full_name, ssn, employment_status, income,
            int(terms_accepted), datetime.now(timezone.utc).isoformat(),
        ),
    )
    conn.commit()
    new_id = cur.lastrowid
    conn.close()
    return new_id


def save_document(owner_username, filename) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT INTO documents (owner_username, filename, uploaded_at) VALUES (?, ?, ?)",
        (owner_username, filename, datetime.now(timezone.utc).isoformat()),
    )
    conn.commit()
    conn.close()


def list_documents(owner_username):
    conn = get_connection()
    rows = conn.execute(
        "SELECT filename, uploaded_at FROM documents WHERE owner_username = ? ORDER BY uploaded_at DESC",
        (owner_username,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def list_applications_paginated(owner_username, page, page_size):
    conn = get_connection()
    total = conn.execute(
        "SELECT COUNT(*) AS c FROM applications WHERE owner_username = ?", (owner_username,)
    ).fetchone()["c"]
    offset = (page - 1) * page_size
    rows = conn.execute(
        "SELECT * FROM applications WHERE owner_username = ? ORDER BY id LIMIT ? OFFSET ?",
        (owner_username, page_size, offset),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows], total


def get_application_owned(app_id, owner_username):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM applications WHERE id = ? AND owner_username = ?", (app_id, owner_username)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_application_any(app_id):
    """Intentionally omits ownership checks -- used only by the /vuln IDOR fixture route."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM applications WHERE id = ?", (app_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def store_token(token: str, username: str) -> None:
    conn = get_connection()
    conn.execute("INSERT OR REPLACE INTO api_tokens (token, username) VALUES (?, ?)", (token, username))
    conn.commit()
    conn.close()


def get_username_for_token(token: str):
    conn = get_connection()
    row = conn.execute("SELECT username FROM api_tokens WHERE token = ?", (token,)).fetchone()
    conn.close()
    return row["username"] if row else None


def increment_balance(username: str, amount) -> None:
    try:
        amount_val = float(amount)
    except (TypeError, ValueError):
        amount_val = 0.0
    conn = get_connection()
    conn.execute(
        "INSERT INTO balances (username, balance) VALUES (?, ?) "
        "ON CONFLICT(username) DO UPDATE SET balance = balance + excluded.balance",
        (username, amount_val),
    )
    conn.commit()
    conn.close()
