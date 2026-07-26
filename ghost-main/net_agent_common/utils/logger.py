"""
Structured logger for Net-Agent.
Matches the style used in Gateway (ghost-main/gateway/app.py).
"""

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)

logger = logging.getLogger("net-agent")
