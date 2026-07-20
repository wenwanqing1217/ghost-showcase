"""Secret scanning script."""

from __future__ import annotations

import re
import sys
from pathlib import Path

_SECRET_PATTERNS = [
    re.compile(r"(?i)(api_key|apikey)\s*[=:]\s*['\"][a-zA-Z0-9_\-]{16,}['\"]"),
    re.compile(r"(?i)(password|passwd|pwd)\s*[=:]\s*['\"][^'\"]{4,}['\"]"),
    re.compile(r"(?i)(secret|token)\s*[=:]\s*['\"][a-zA-Z0-9_\-\.]{8,}['\"]"),
    re.compile(r"(?i)(aws_access_key_id|aws_secret_access_key)\s*[=:]\s*['\"][a-zA-Z0-9/+=]+['\"]"),
    re.compile(r"(?i)(private_key|BEGIN\s+(RSA|DSA|EC|OPENSSH)\s+PRIVATE\s+KEY)"),
]


def scan(path: Path) -> bool:
    """Scan path for secrets. Returns True if clean."""
    clean = True
    for file in sorted(path.rglob("*.py")):
        if any(part.startswith(".") and part not in {".env.example"} for part in file.parts):
            continue
        text = file.read_text(encoding="utf-8", errors="ignore")
        for pattern in _SECRET_PATTERNS:
            matches = pattern.findall(text)
            if matches:
                clean = False
                print(f"SECRET FOUND in {file}: {len(matches)} matches")
    return clean


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    if not scan(root):
        return 1
    print("No secrets found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
