r"""
ObsidianWriter — Auto-sync Alpha-ID memories to Obsidian vault
===============================================================
Reads from MemoryStore (via Gateway API) and writes formatted .md files
to the Obsidian vault at D:\Obsidian\Ghost知识库.

Each memory becomes a note with YAML frontmatter:
  ---
  title: Memory title
  date: 2026-07-25
  tags: [doubao, chat, ...]
  category: doubao_chat
  source: doubao
  memory_id: abc123
  ---

Run modes:
  1. Daemon: polls Gateway periodically for new memories
  2. One-shot: process a single memory dict
"""

import os
import json
import re
import time
import logging
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

logger = logging.getLogger("obsidian_writer")

# Allowlist pattern for category names: alphanumeric, underscore, hyphen only
_CATEGORY_RE = re.compile(r"^[\w-]+$")


def _yaml_scalar(value: Any) -> str:
    """
    Safely serialize a value as a YAML scalar.
    Wraps strings containing special characters in double quotes
    to prevent YAML frontmatter injection.
    """
    s = str(value)
    # Characters that require quoting in YAML plain scalars
    if not s:
        return '""'
    needs_quote = any(c in s for c in ':{}[]&*?|-><!%@`#,\'"\\') or s[0] in "-?#"
    if needs_quote:
        # Escape backslashes and double quotes
        escaped = s.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return s

# Config
VAULT_PATH = os.getenv("OBSIDIAN_VAULT", r"D:\Obsidian\Ghost知识库")
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost:18080")
POLL_INTERVAL = int(os.getenv("OBSIDIAN_POLL_INTERVAL", "300"))  # 5 min
STATE_FILE = Path.home() / ".obsidian_writer_state.json"


class ObsidianWriter:
    """Write memories to Obsidian vault as formatted .md files."""

    def __init__(self, vault_path: str = VAULT_PATH):
        self.vault = Path(vault_path)
        self.vault.mkdir(parents=True, exist_ok=True)

    def write_memory(self, data: Dict[str, Any]) -> Optional[Path]:
        """
        Write a single memory entry as an .md file.
        
        Args:
            data: Memory dict with keys: content, category, tags, source, memory_id, timestamp
        
        Returns:
            Path to the written file, or None if failed
        """
        content = data.get("content", "")
        if not content:
            logger.warning("Empty content, skipping")
            return None

        memory_id = data.get("memory_id", f"mem_{int(time.time())}_{os.getpid()}")
        category = data.get("category", "general")
        tags = data.get("tags", [])
        source = data.get("source", "unknown")
        timestamp = data.get("timestamp", time.time())

        # --- Path traversal prevention ---
        # Reject any category containing path separators or parent-dir references.
        if not _CATEGORY_RE.match(category):
            logger.warning("Invalid category rejected: %r", category)
            category = "general"

        dt = datetime.fromtimestamp(timestamp)
        date_str = dt.strftime("%Y-%m-%d")
        time_str = dt.strftime("%H:%M:%S")

        # Create category subfolder (safe: category validated against allowlist)
        cat_dir = self.vault / category.replace("_", "-")
        cat_dir.mkdir(exist_ok=True)
        
        # Create date subfolder
        date_dir = cat_dir / date_str
        date_dir.mkdir(exist_ok=True)
        
        # Generate title from content
        title = content.strip()[:60]
        if len(content) > 60:
            title += "..."
        # Clean filename
        safe_title = "".join(c for c in title if c.isalnum() or c in " -_.,!?").strip()[:50]
        
        filename = f"{date_str} {safe_title} [{memory_id[:8]}].md"
        filepath = date_dir / filename
        
        # Build frontmatter
        frontmatter = {
            "title": title,
            "date": date_str,
            "time": time_str,
            "memory_id": memory_id,
            "category": category,
            "source": source,
            "tags": tags if isinstance(tags, list) else [tags],
        }

        # Build note content with proper YAML escaping
        note = "---\n"
        for k, v in frontmatter.items():
            if isinstance(v, list):
                note += f"{k}:\n"
                for item in v:
                    note += f"  - {_yaml_scalar(item)}\n"
            else:
                note += f"{k}: {_yaml_scalar(v)}\n"
        note += "---\n\n"
        note += f"# {_yaml_scalar(title)}\n\n"
        note += content + "\n"

        # Add cross-links
        note += "\n---\n"
        note += f"来源: [[{source}]]  |  分类: [[{category}]]  |  captured: {date_str} {time_str}\n"

        # Atomic write: write to temp file then rename (prevents partial writes)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(
            dir=str(filepath.parent), suffix=".tmp", prefix=".ow_"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(note)
            os.replace(tmp_path, str(filepath))
        except Exception:
            # Clean up temp file on failure
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

        logger.info("Written: %s", filepath)
        return filepath

    def write_conversation(self, metadata: Dict[str, Any], messages: list, 
                           session_id: str, bot_id: str = "") -> Optional[Path]:
        """Write a full conversation as a formatted note."""
        dt = datetime.now()
        date_str = dt.strftime("%Y-%m-%d")
        
        title = f"豆包对话 {session_id[:12]}"
        if messages:
            first_msg = messages[0].get("content", "")[:40]
            title = f"豆包: {first_msg}"
        
        safe_title = "".join(c for c in title if c.isalnum() or c in " -_,").strip()[:45]
        filename = f"豆包对话 {date_str} [{safe_title}].md"
        
        dir_path = self.vault / "doubao-chat" / date_str
        dir_path.mkdir(parents=True, exist_ok=True)
        filepath = dir_path / filename

        # Build note with proper YAML escaping
        note = "---\n"
        note += f"title: {_yaml_scalar(title)}\n"
        note += f"date: {_yaml_scalar(date_str)}\n"
        note += "source: doubao\n"
        note += f"bot_id: {_yaml_scalar(bot_id)}\n"
        note += f"session_id: {_yaml_scalar(session_id)}\n"
        note += f"message_count: {len(messages)}\n"
        note += "tags:\n"
        note += "  - doubao\n"
        note += "  - chat\n"
        if bot_id:
            note += f"  - {_yaml_scalar(f'bot_{bot_id}')}\n"
        note += "---\n\n"
        note += f"# {_yaml_scalar(title)}\n\n"

        for i, msg in enumerate(messages):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            emoji = "👤" if role == "user" else "🤖"
            note += f"### {emoji} {role.upper()}\n\n{content}\n\n"

        note += f"\n---\n会话ID: {session_id} | 捕获时间: {date_str}\n"

        # Atomic write
        filepath.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(
            dir=str(filepath.parent), suffix=".tmp", prefix=".ow_"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(note)
            os.replace(tmp_path, str(filepath))
        except Exception:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
            raise

        logger.info("Conversation written: %s", filepath)
        return filepath


def poll_gateway():
    """Daemon mode: poll Gateway for new memories periodically."""
    writer = ObsidianWriter()
    state = {"last_memory_id": ""}

    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass

    logger.info("ObsidianWriter daemon starting (vault: %s)", VAULT_PATH)

    # NOTE: This daemon is currently a placeholder. The Gateway push
    # integration is not yet implemented. The loop below simply sleeps
    # until the feature is wired up.
    while True:
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Quick test: write a sample memory
    writer = ObsidianWriter()
    path = writer.write_memory({
        "content": "测试豆包记忆同步到Obsidian",
        "category": "doubao_chat",
        "tags": ["doubao", "test"],
        "source": "doubao",
        "memory_id": "test001",
        "timestamp": time.time(),
    })
    print(f"Test written to: {path}")
