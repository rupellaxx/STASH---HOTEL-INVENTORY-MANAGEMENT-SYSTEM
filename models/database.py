"""
models/database.py
──────────────────
Pure database layer: connection factory + low-level query helpers.
Password hashing lives here (hashlib / SHA-256) so every model
that needs it imports from one place.
"""

import hashlib
import mysql.connector
from mysql.connector import Error

# ── Connection settings ───────────────────────────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",
    "database": "hotel_db",
    "user":     "root",
    "password": "",
}


# ── Password helper ───────────────────────────────────────────────────────────
def hash_password(plain: str) -> str:
    """
    Hash *plain* with Python's built-in hashlib (SHA-256).
    Returns a 64-character hex-digest string.
    """
    return hashlib.sha256(plain.encode("utf-8")).hexdigest()


# ── Connection factory ────────────────────────────────────────────────────────
def get_connection() -> mysql.connector.MySQLConnection:
    """Return a live MySQL connection using DB_CONFIG."""
    return mysql.connector.connect(**DB_CONFIG)


# ── Query helpers ─────────────────────────────────────────────────────────────
def fetch_all(query: str, params: tuple = ()) -> list[dict]:
    """Execute *query* and return all rows as a list of dicts."""
    conn = get_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def fetch_one(query: str, params: tuple = ()) -> dict | None:
    """Execute *query* and return the first row as a dict, or None."""
    conn = get_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute(query, params)
    row  = cur.fetchone()
    cur.close()
    conn.close()
    return row


def execute_query(query: str, params: tuple = ()) -> int:
    """
    Execute an INSERT / UPDATE / DELETE statement.
    Returns the last inserted row-id (useful for INSERT).
    """
    conn    = get_connection()
    cur     = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    last_id = cur.lastrowid
    cur.close()
    conn.close()
    return last_id