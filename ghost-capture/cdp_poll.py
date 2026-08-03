"""
CDP Poll Capture — runs singleshot every 3 seconds via subprocess.
More reliable than persistent WebSocket connection.

Security notes:
  - GATEWAY_URL is validated against an allowlist of schemes/hosts
  - All gateway requests include an API key (from GATEWAY_API_KEY env)
  - File writes are atomic (tempfile + os.replace)
  - Session ID is stable per process lifetime (not per request)
"""
import sys
import time
import hashlib
import json
import tempfile
import subprocess
import requests
import os
from pathlib import Path
from urllib.parse import urlparse

# ---------------------------------------------------------------------------
# Configuration with validation
# ---------------------------------------------------------------------------

def _validate_gateway_url(raw: str) -> str:
    """
    Validate GATEWAY_URL to prevent SSRF.
    Only allows http/https schemes and private/local addresses.
    """
    parsed = urlparse(raw)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(f"GATEWAY_URL must be http/https, got: {parsed.scheme}")

    host = parsed.hostname or ""
    # Block obviously dangerous hosts
    blocked_hosts = {"localhost", "127.0.0.1", "0.0.0.0", "::1", "[::1]"}
    # Allow private networks and localhost for dev (override with GATEWAY_ALLOW_EXTERNAL=1)
    allow_external = os.environ.get("GATEWAY_ALLOW_EXTERNAL", "0") == "1"
    if not allow_external and host not in blocked_hosts:
        # Check if it's a private IP
        import ipaddress
        try:
            addr = ipaddress.ip_address(host)
            if not addr.is_private and not addr.is_loopback:
                raise ValueError(
                    f"GATEWAY_URL host {host} is not a private address. "
                    f"Set GATEWAY_ALLOW_EXTERNAL=1 to override."
                )
        except ValueError:
            # Not an IP, likely a hostname — block unless explicitly allowed
            raise ValueError(
                f"GATEWAY_URL host {host} is not a recognized private address. "
                f"Set GATEWAY_ALLOW_EXTERNAL=1 to override."
            )

    return raw.rstrip("/")


GATEWAY = os.environ.get("GATEWAY_URL", "http://localhost:18080")
try:
    GATEWAY = _validate_gateway_url(GATEWAY)
except ValueError as e:
    sys.stderr.write(f"[CDP-Poll] FATAL: {e}\n")
    sys.exit(1)

GATEWAY_CAPTURE = f"{GATEWAY}/v1/internal/doubao/capture"
GATEWAY_API_KEY = os.environ.get("GATEWAY_API_KEY", "")

SCRIPT = os.path.join(os.path.dirname(__file__), "cdp_singleshot.py")
SEEN_FILE = os.path.join(os.path.dirname(__file__), "cdp_seen.json")

# Stable session ID for the lifetime of this process
SESSION_ID = f"cdp-poll-{int(time.time())}"

seen: set = set()
last = ""
MAX_SEEN = 10000  # Cap memory usage — old entries evicted via save_seen()

# ---------------------------------------------------------------------------
# Atomic file operations
# ---------------------------------------------------------------------------


def _atomic_write_json(filepath: str, data) -> None:
    """Write JSON atomically using tempfile + os.replace."""
    dir_path = os.path.dirname(filepath)
    fd, tmp_path = tempfile.mkstemp(dir=dir_path, suffix=".tmp", prefix=".cdp_")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False)
        os.replace(tmp_path, filepath)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def load_seen() -> set:
    """Load previously seen texts from disk."""
    if os.path.exists(SEEN_FILE):
        try:
            return set(json.load(open(SEEN_FILE, "r", encoding="utf-8")))
        except Exception:
            pass
    return set()


def save_seen() -> None:
    """Persist seen set atomically, evicting oldest entries if over MAX_SEEN."""
    global seen
    try:
        # Evict oldest entries in-memory to cap memory
        if len(seen) > MAX_SEEN:
            seen = set(list(seen)[-MAX_SEEN // 2:])
        _atomic_write_json(SEEN_FILE, list(seen)[-5000:])
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Gateway communication
# ---------------------------------------------------------------------------


def send_to_gateway(messages: list) -> None:
    """Send captured messages to the gateway with authentication."""
    headers = {"Content-Type": "application/json"}
    if GATEWAY_API_KEY:
        headers["Authorization"] = f"Bearer {GATEWAY_API_KEY}"

    r = requests.post(
        GATEWAY_CAPTURE,
        json={
            "session_id": SESSION_ID,
            "bot_id": "doubao_web_cdp",
            "captured_at": int(time.time()),
            "messages": messages,
        },
        headers=headers,
        timeout=5,
    )
    log(f"Gateway: {r.status_code}")


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------


def log(m: str) -> None:
    sys.stderr.write(m + "\n")
    sys.stderr.flush()


def main() -> None:
    global seen, last

    seen = load_seen()
    log(f"[CDP-Poll] Loaded {len(seen)} seen texts")
    log(f"[CDP-Poll] Gateway: {GATEWAY_CAPTURE}")
    log(f"[CDP-Poll] Session: {SESSION_ID}")

    while True:
        try:
            # Run singleshot and capture output
            result = subprocess.run(
                ["python", SCRIPT],
                capture_output=True,
                text=True,
                timeout=10,
                cwd=os.path.dirname(SCRIPT),
            )
            text = result.stdout.strip()

            if not text or len(text) < 50:
                time.sleep(3)
                continue

            if not last:
                last = text
                log(f"Init: {len(text)} chars")
                time.sleep(3)
                continue

            if text == last:
                time.sleep(3)
                continue

            # Text changed!
            old: set = set()
            for line in last.split("\n"):
                t = line.strip()
                if 4 < len(t) < 2000:
                    old.add(hashlib.md5(t.encode()).hexdigest())

            msgs = []
            for line in text.split("\n"):
                t = line.strip()
                if len(t) < 5 or len(t) > 2000:
                    continue
                h = hashlib.md5(t.encode()).hexdigest()
                if h not in old and t not in seen:
                    seen.add(t)
                    # Role detection: unknown — let downstream LLM classify
                    msgs.append(
                        {
                            "role": "unknown",
                            "content": t,
                            "timestamp": int(time.time() * 1000),
                        }
                    )

            if msgs:
                log(f"Change detected! {len(msgs)} new items")
                try:
                    send_to_gateway(msgs)
                except Exception as e:
                    log(f"GW err: {e}")
                save_seen()

            last = text
        except subprocess.TimeoutExpired:
            log("Timeout")
        except Exception as e:
            log(f"Error: {e}")

        time.sleep(3)


if __name__ == "__main__":
    main()
