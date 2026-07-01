"""
database.py — permanent local storage using SQLite.

The database file lives in the user's home folder under ".adina_meetings",
so it persists across app restarts and updates. Each saved booking stores both
its summary figures and its full itemised lines (as JSON) for later export.
"""

import sqlite3
import json
import os
from pathlib import Path
from datetime import datetime


def data_dir() -> Path:
    """A stable per-user folder that works on Windows and macOS."""
    home = Path.home()
    d = home / ".adina_meetings"
    d.mkdir(parents=True, exist_ok=True)
    return d


DB_PATH = data_dir() / "bookings.db"


def _connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                row_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id  TEXT,
                customer    TEXT,
                qty         INTEGER,
                unit        TEXT,
                package     TEXT,
                event_date  TEXT,
                net         REAL,
                vat7        REAL,
                vat19       REAL,
                gross       REAL,
                adjust      REAL,
                adjust_note TEXT,
                total       REAL,
                lines_json  TEXT,
                services_json TEXT,
                created_at  TEXT
            )
        """)


def save_booking(b) -> int:
    """Persist a computed Booking; returns its database row id."""
    with _connect() as conn:
        cur = conn.execute("""
            INSERT INTO bookings
            (booking_id, customer, qty, unit, package, event_date,
             net, vat7, vat19, gross, adjust, adjust_note, total,
             lines_json, services_json, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            b.booking_id, b.customer, b.qty, b.unit, b.package, b.event_date,
            b.net, b.vat7, b.vat19, b.gross, b.adjust, b.adjust_note, b.total,
            json.dumps(b.lines), json.dumps(b.services),
            datetime.now().isoformat(timespec="seconds"),
        ))
        return cur.lastrowid


def load_all():
    """Return all saved bookings, newest first, as a list of dicts."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM bookings ORDER BY row_id DESC").fetchall()
    return [dict(r) for r in rows]


def delete_booking(row_id: int):
    with _connect() as conn:
        conn.execute("DELETE FROM bookings WHERE row_id = ?", (row_id,))


def clear_all():
    with _connect() as conn:
        conn.execute("DELETE FROM bookings")


def next_seq_for_date(event_date: str) -> int:
    """How many bookings already exist for this event date (for auto-ID)."""
    like = event_date or ""
    with _connect() as conn:
        n = conn.execute(
            "SELECT COUNT(*) FROM bookings WHERE event_date = ?",
            (like,)).fetchone()[0]
    return n + 1
