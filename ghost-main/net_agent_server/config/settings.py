"""
Net-Agent Server Configuration
===============================
All settings come from environment variables with sensible defaults.
"""

import os
from pathlib import Path

# ── paths ────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = os.getenv("NET_AGENT_DB", str(BASE_DIR / "data" / "net_agent.db"))

# ── server ───────────────────────────────────────────────────
NET_AGENT_PORT = int(os.getenv("NET_AGENT_PORT", "18180"))
NET_AGENT_HOST = os.getenv("NET_AGENT_HOST", "0.0.0.0")

# ── security ─────────────────────────────────────────────────
# AES master key for encrypting router credentials (32 bytes hex)
AES_MASTER_KEY = os.getenv("NET_AGENT_AES_KEY", "")
# JWT secret — should match Alpha-ID's secret for token compatibility
JWT_SECRET = os.getenv("NET_AGENT_JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = int(os.getenv("NET_AGENT_JWT_EXPIRE", "24"))

# ── scanner ──────────────────────────────────────────────────
SCAN_INTERVAL_SECONDS = int(os.getenv("NET_AGENT_SCAN_INTERVAL", "3600"))  # hourly
PING_TARGETS = ["223.5.5.5", "8.8.8.8", "114.114.114.114"]  # AliDNS, Google, 114

# ── tunnel ───────────────────────────────────────────────────
TUNNEL_TYPE = os.getenv("NET_AGENT_TUNNEL", "tailscale")  # tailscale / frp

# ── upstream services ───────────────────────────────────────
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:18080")
ALPHAID_URL = os.getenv("ALPHAID_URL", "http://localhost:8000")
NEBULA_URL = os.getenv("NEBULA_URL", "http://localhost:2002")
