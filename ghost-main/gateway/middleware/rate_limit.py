"""Rate limiting utilities — in-memory sliding window (thread-safe)."""

import os
import threading
import time
from collections import defaultdict

from fastapi import Request

# Rate limit configuration
_rate_buckets: dict = defaultdict(list)
_rate_lock = threading.Lock()  # Protects _rate_buckets from concurrent access
_RATE_LIMIT_MAX = int(os.getenv("RATE_LIMIT_MAX", "5"))
_RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
# Cap total keys to prevent memory leak from unbounded IP growth
_MAX_BUCKETS = 10000


def rate_limit_check(key: str, max_requests: int = None, window: int = None) -> bool:
    """Check rate limit. Returns True if allowed, False if exceeded.

    Thread-safe: uses a lock to protect the shared _rate_buckets dict.
    """
    now = time.time()
    max_req = max_requests or _RATE_LIMIT_MAX
    win = window or _RATE_LIMIT_WINDOW

    with _rate_lock:
        # Evict old entries
        bucket = _rate_buckets[key]
        cutoff = now - win
        _rate_buckets[key] = [t for t in bucket if t > cutoff]

        if len(_rate_buckets[key]) >= max_req:
            return False
        _rate_buckets[key].append(now)

        # Memory protection: if too many keys, clear oldest buckets
        if len(_rate_buckets) > _MAX_BUCKETS:
            # Remove buckets with oldest entries (simple eviction)
            sorted_keys = sorted(_rate_buckets, key=lambda k: max(_rate_buckets[k]) if _rate_buckets[k] else 0)
            for old_key in sorted_keys[:len(_rate_buckets) // 4]:
                del _rate_buckets[old_key]

        return True


def reset_rate_limits():
    """Reset all rate limit buckets (for testing)."""
    with _rate_lock:
        _rate_buckets.clear()


def client_ip(request: Request) -> str:
    """Get client real IP (proxy-aware)."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
