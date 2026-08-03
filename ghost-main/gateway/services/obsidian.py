"""Obsidian vault operations."""

import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from doubao_reader.obsidian_writer import ObsidianWriter
from doubao_reader.obsidian_organizer import run_organization, batch_link_related

logger = logging.getLogger("ghost-gateway")


def get_vault_path() -> str:
    """Get Obsidian vault path from environment."""
    # 默认路径与 doubao_reader/obsidian_writer.py / obsidian_organizer.py 保持一致
    return os.environ.get(
        "OBSIDIAN_VAULT", r"D:\Obsidian\Ghost知识库"
    )


def check_vault_status() -> Dict[str, Any]:
    """Check Obsidian vault status."""
    vault_path = get_vault_path()
    exists = os.path.isdir(vault_path)
    file_count = 0
    recent_file = ""
    recent_mtime = 0.0
    if exists:
        for root, dirs, files in os.walk(vault_path):
            for f in files:
                if f.endswith(".md"):
                    file_count += 1
                    fpath = os.path.join(root, f)
                    try:
                        mtime = os.path.getmtime(fpath)
                    except OSError:
                        continue
                    if mtime > recent_mtime:
                        recent_mtime = mtime
                        recent_file = f
    return {
        "exists": exists,
        "path": vault_path,
        "file_count": file_count,
        "recent_file": recent_file,
    }


def search_vault(keyword: str = "", limit: int = 20) -> List[Dict[str, Any]]:
    """Search the Obsidian vault for memories matching keyword."""
    vault_path = get_vault_path()
    results = []

    for root, dirs, files in os.walk(vault_path):
        for fname in files:
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(root, fname)
            try:
                text = open(fpath, "r", encoding="utf-8").read()
            except Exception:
                continue

            title = fname.replace(".md", "")
            category = os.path.basename(os.path.dirname(fpath))
            date_str = ""
            tags = []

            if text.startswith("---"):
                end_idx = text.find("---", 3)
                if end_idx > 0:
                    fm = text[3:end_idx]
                    for line in fm.split("\n"):
                        line = line.strip()
                        if line.startswith("title:"):
                            title = line.split(":", 1)[1].strip().strip('"')
                        elif line.startswith("date:"):
                            date_str = line.split(":", 1)[1].strip()
                        elif line.startswith("  - "):
                            tags.append(line[4:].strip())

            content_text = text
            if keyword:
                if keyword.lower() not in content_text.lower():
                    continue
                kw_lower = keyword.lower()
                ctx = max(0, content_text.lower().find(kw_lower) - 100)
                content_text = content_text[ctx : ctx + 250]

            results.append(
                {
                    "title": title,
                    "file": fname,
                    "category": category,
                    "date": date_str,
                    "tags": tags,
                    "preview": content_text[:300],
                    "modified": os.path.getmtime(fpath),
                }
            )

            if len(results) >= limit:
                break
        if len(results) >= limit:
            break

    results.sort(key=lambda r: r["modified"], reverse=True)
    return results


def get_feeds(industry: Optional[str] = None, limit: int = 20) -> List[Dict[str, Any]]:
    """Get latest industry-curated info from Obsidian feeds directory."""
    vault_path = get_vault_path()
    feeds_dir = os.path.join(vault_path, "feeds") if vault_path else ""
    if not os.path.isdir(feeds_dir):
        return []

    feeds = []
    for root, dirs, files in os.walk(feeds_dir):
        for fname in files:
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(root, fname)
            try:
                text = open(fpath, "r", encoding="utf-8").read()
            except Exception:
                continue
            if industry and industry.lower() not in text.lower():
                continue
            title = fname.replace(".md", "")
            category = os.path.basename(os.path.dirname(fpath))
            feeds.append(
                {
                    "title": title,
                    "category": category,
                    "preview": text[:500],
                    "updated_at": os.path.getmtime(fpath),
                    "content": text,
                }
            )
            if len(feeds) >= limit:
                break
        if len(feeds) >= limit:
            break

    feeds.sort(key=lambda r: r["updated_at"], reverse=True)
    return feeds


def write_conversation_async(
    metadata: dict, messages: list, session_id: str, bot_id: str = ""
):
    """Write conversation to Obsidian vault in background executor."""
    try:
        import asyncio

        ow = ObsidianWriter()
        loop = asyncio.get_event_loop()
        loop.run_in_executor(
            None,
            lambda: ow.write_conversation(
                metadata=metadata,
                messages=messages,
                session_id=session_id,
                bot_id=bot_id,
            ),
        )
    except Exception as ow_err:
        logger.warning("Obsidian write failed (non-fatal): %s", ow_err)


def trigger_organization():
    """Trigger Obsidian organization in background thread."""
    try:
        import threading

        threading.Thread(target=run_organization, daemon=True).start()
    except Exception as org_err:
        logger.debug("Organization trigger error: %s", org_err)


def run_batch_link():
    """Run batch link related files in Obsidian vault."""
    try:
        batch_link_related()
    except Exception as org_err:
        logger.error("Batch link error: %s", org_err)
