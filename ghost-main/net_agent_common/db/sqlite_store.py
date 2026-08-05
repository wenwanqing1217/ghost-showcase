"""
SQLite Store — thin wrapper around sqlite3.
============================================
Connection-per-request pattern with FastAPI dependency injection.
"""

# Ensure directory exists
import os
import sqlite3
import time
from contextlib import contextmanager

from net_agent_common.config.settings import DB_PATH

from .models import init_db

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# Module-level: create the DB if not present
_conn = sqlite3.connect(DB_PATH)
init_db(_conn)
_conn.close()


@contextmanager
def get_connection():
    """Yield a sqlite3 connection with Row factory."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # better concurrent reads
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def now() -> int:
    """Current unix timestamp."""
    return int(time.time())
