import os
import sys
import json
import time
import logging
import requests
from pathlib import Path
from datetime import datetime

# Add parent dir to path so log_reader can be imported
sys.path.insert(0, str(Path(__file__).parent))
from log_reader import LogReader

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
logger = logging.getLogger("doubao-daemon")

GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:18080")
POLL_INTERVAL_SEC = int(os.getenv("DOUBAO_POLL_INTERVAL", "60"))  # 1 min default
STATE_FILE = Path.home() / ".doubao_daemon_state.json"

class DaemonState:
    def __init__(self):
        self.last_captured_at: int = 0
        self.seen_sessions: set = set()
        self._load()
    
    def _load(self):
        if STATE_FILE.exists():
            try:
                data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
                self.last_captured_at = data.get("last_captured_at", 0)
                self.seen_sessions = set(data.get("seen_sessions", []))
            except Exception:
                pass
    
    def save(self):
        STATE_FILE.write_text(json.dumps({
            "last_captured_at": self.last_captured_at,
            "seen_sessions": list(self.seen_sessions),
        }, ensure_ascii=False), encoding="utf-8")


def send_to_gateway(conv_dict: dict) -> bool:
    url = f"{GATEWAY_URL}/v1/doubao/capture"
    try:
        resp = requests.post(url, json=conv_dict, timeout=10)
        data = resp.json()
        if data.get("success"):
            logger.info("Sent: %s (%d msgs)", conv_dict.get("session_id","?"), len(conv_dict.get("messages",[])))
            return True
        else:
            logger.warning("Gateway error: %s", data.get("error", "unknown"))
            return False
    except requests.RequestException as e:
        logger.warning("Gateway unreachable: %s", e)
        return False


def main():
    logger.info("Doubao Daemon starting...")
    logger.info("Gateway: %s", GATEWAY_URL)
    logger.info("Poll interval: %ds", POLL_INTERVAL_SEC)
    
    reader = LogReader()
    state = DaemonState()
    
    while True:
        try:
            convs = reader.read_all()
            if not convs:
                logger.debug("No new conversations found")
            
            for conv in convs:
                conv_dict = conv.to_dict()
                session_id = conv_dict.get("session_id", "")
                
                # Dedup check
                if session_id and session_id in state.seen_sessions:
                    continue
                
                # Send to Gateway
                if send_to_gateway(conv_dict):
                    if session_id:
                        state.seen_sessions.add(session_id)
                    state.last_captured_at = int(time.time())
                    state.save()
            
        except Exception as e:
            logger.error("Poll failed: %s", e, exc_info=True)
        
        time.sleep(POLL_INTERVAL_SEC)


if __name__ == "__main__":
    main()
