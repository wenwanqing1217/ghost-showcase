"""
Database Models & Schema
=========================
SQLite with row-level isolation (every table has user_id).
"""

SCHEMA_SQL = """
-- User router configuration (one row per user)
CREATE TABLE IF NOT EXISTS user_router_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    vendor TEXT NOT NULL,                    -- openwrt / xiaomi / tplink
    lan_address TEXT NOT NULL,               -- router LAN IP (e.g. 192.168.1.1)
    encrypted_username TEXT NOT NULL,         -- AES-GCM ciphertext dict (JSON)
    encrypted_password TEXT NOT NULL,         -- AES-GCM ciphertext dict (JSON)
    salt TEXT NOT NULL,                      -- unique per user
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    UNIQUE(user_id)
);

-- Network inspection logs (hourly snapshots)
CREATE TABLE IF NOT EXISTS network_inspect_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    latency_ms REAL DEFAULT 0,
    packet_loss_pct REAL DEFAULT 0,
    jitter_ms REAL DEFAULT 0,
    online_devices_count INTEGER DEFAULT 0,
    network_score INTEGER DEFAULT 100,
    raw_data TEXT                            -- JSON blob for extra fields
);

-- Operation audit log (reboot, ban, channel switch, etc.)
CREATE TABLE IF NOT EXISTS operation_audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    action TEXT NOT NULL,                    -- reboot / ban_mac / set_channel / ...
    trigger_type TEXT NOT NULL,              -- manual / rule / llm
    result TEXT NOT NULL,                    -- success / failure
    detail TEXT,                             -- error message or extra info
    operated_at INTEGER NOT NULL
);

-- Task queue (server → client commands)
CREATE TABLE IF NOT EXISTS user_task_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    task_type TEXT NOT NULL,                 -- reboot / refresh_status / scan_devices
    task_body TEXT,                          -- JSON payload
    status TEXT NOT NULL DEFAULT 'pending',  -- pending / claimed / done / failed
    created_at INTEGER NOT NULL,
    claimed_at INTEGER,
    completed_at INTEGER
);

-- Known devices (user-marked as recognised)
CREATE TABLE IF NOT EXISTS known_devices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    mac TEXT NOT NULL,
    name TEXT,
    first_seen INTEGER NOT NULL,
    UNIQUE(user_id, mac)
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_inspect_user_time
    ON network_inspect_logs(user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_user_time
    ON operation_audit_logs(user_id, operated_at DESC);
CREATE INDEX IF NOT EXISTS idx_task_user_status
    ON user_task_queue(user_id, status);
CREATE INDEX IF NOT EXISTS idx_known_user
    ON known_devices(user_id);
"""


def init_db(conn):
    """Create all tables if they don't exist."""
    conn.executescript(SCHEMA_SQL)
    conn.commit()
