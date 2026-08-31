"""Tiny SQLite-backed store tracking one status row per calendar day.

Kept deliberately simple: a single table, one row per date, so a bot
restart mid-afternoon doesn't lose track of whether today's meeting was
already confirmed or cancelled.
"""
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

_SCHEMA = """
CREATE TABLE IF NOT EXISTS daily_status (
    date TEXT PRIMARY KEY,
    status TEXT NOT NULL,       -- 'pending' | 'confirmed' | 'cancelled'
    message_ts TEXT,
    confirmed_by TEXT,
    confirmed_at TEXT
);
"""


@dataclass
class DayRecord:
    date: str
    status: str
    message_ts: Optional[str] = None
    confirmed_by: Optional[str] = None
    confirmed_at: Optional[str] = None


class StateStore:
    def __init__(self, db_path: str):
        self._db_path = db_path
        with closing(self._connect()) as conn:
            conn.execute(_SCHEMA)
            conn.commit()

    def _connect(self):
        return sqlite3.connect(self._db_path)

    def start_new_day(self, date: str, message_ts: str) -> None:
        """Called when the reminder is posted.

        Resets any stale row for this date.
        """
        with closing(self._connect()) as conn:
            conn.execute(
                "INSERT OR REPLACE INTO daily_status "
                "(date, status, message_ts, confirmed_by, confirmed_at) "
                "VALUES (?, 'pending', ?, NULL, NULL)",
                (date, message_ts),
            )
            conn.commit()

    def get(self, date: str) -> Optional[DayRecord]:
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT date, status, message_ts, confirmed_by, confirmed_at "
                "FROM daily_status WHERE date = ?",
                (date,),
            ).fetchone()
        return DayRecord(*row) if row else None

    def confirm(self, date: str, user_id: str) -> bool:
        """Mark today confirmed. Returns False if nothing was pending
        (already confirmed by someone else, already cancelled, or no
        reminder posted)."""
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT status FROM daily_status WHERE date = ?", (date,)
            ).fetchone()
            if row is None or row[0] != "pending":
                return False
            conn.execute(
                "UPDATE daily_status SET status = 'confirmed', confirmed_by = ?, "
                "confirmed_at = ? WHERE date = ?",
                (user_id, datetime.now(timezone.utc).isoformat(), date),
            )
            conn.commit()
            return True

    def cancel_if_pending(self, date: str) -> bool:
        """Called at the cutoff.

        Returns True if it flipped pending -> cancelled (nobody had
        confirmed), False if it was already confirmed/cancelled/missing.
        """
        with closing(self._connect()) as conn:
            row = conn.execute(
                "SELECT status FROM daily_status WHERE date = ?", (date,)
            ).fetchone()
            if row is None or row[0] != "pending":
                return False
            conn.execute(
                "UPDATE daily_status SET status = 'cancelled' WHERE date = ?", (date,)
            )
            conn.commit()
            return True
