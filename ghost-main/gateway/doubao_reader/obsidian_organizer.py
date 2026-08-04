"""
Obsidian Auto-Organizer — auto-link, auto-index, auto-summarize
================================================================
Runs periodically after new memories are written.
Zero LLM tokens — pure rule-based linking.

Features:
  1. Auto-generate [[wiki-links]] between related notes
  2. Daily summary pages ("2026-07-25 日报")
  3. Tag-based index pages (自动索引页)
  4. Cross-reference by keywords
"""

import os
import re
import time
import logging
import hashlib
from pathlib import Path
from datetime import datetime, date
from typing import List, Dict, Set, Optional
from collections import defaultdict

logger = logging.getLogger("obsidian_organizer")

VAULT_PATH = os.environ.get("OBSIDIAN_VAULT", r"D:\Obsidian\Ghost知识库")

# ── Keyword groups for cross-linking ──
TOPIC_GROUPS = {
    "code": ["python", "javascript", "typescript", "代码", "编程", "函数", "class", "api"],
    "design": ["设计", "ui", "ux", "界面", "样式", "css", "布局", "颜色"],
    "architecture": ["架构", "系统", "框架", "模块", "组件", "服务", "部署"],
    "knowledge": ["知识", "记忆", "学习", "笔记", "文档", "obsidian", "图谱"],
    "project": ["项目", "需求", "方案", "计划", "迭代", "版本", "feature"],
    "bot": ["飞书", "bot", "机器人", "总助", "atomcode", "codex"],
    "doubao": ["豆包", "doubao", "对话", "聊天"],
}

# ── Stop words for link text ──
STOP_WORDS = {"的", "了", "是", "在", "有", "和", "就", "不", "人", "都", "一", "一个", "上", "也", "很", "到", "说", "要", "去", "你", "会", "着", "没有", "看", "好", "自己", "这"}


def extract_keywords(text: str, max_keywords: int = 5) -> List[str]:
    """Extract meaningful keywords from text."""
    # Find Chinese/English words
    words = re.findall(r"[\u4e00-\u9fff\w]+", text)
    # Filter stop words and short ones
    keywords = [w for w in words if len(w) > 1 and w.lower() not in STOP_WORDS]
    # Dedup preserving order
    seen = set()
    result = []
    for w in keywords:
        if w not in seen:
            seen.add(w)
            result.append(w)
    return result[:max_keywords]


def compute_similarity(text1: str, text2: str) -> float:
    """Compute simple keyword overlap similarity (0.0 - 1.0)."""
    kw1 = set(extract_keywords(text1, 20))
    kw2 = set(extract_keywords(text2, 20))
    if not kw1 or not kw2:
        return 0.0
    intersection = kw1 & kw2
    return len(intersection) / max(len(kw1), len(kw2))


def find_related_notes(target_path: Path, all_notes: List[Dict], threshold: float = 0.15) -> List[Dict]:
    """Find notes related to target based on keyword overlap."""
    target_text = target_path.read_text(encoding="utf-8", errors="ignore")
    results = []
    for note in all_notes:
        if Path(note["path"]) == target_path:
            continue
        sim = compute_similarity(target_text, note["content"])
        if sim >= threshold:
            note["similarity"] = round(sim, 3)
            results.append(note)
    results.sort(key=lambda x: x["similarity"], reverse=True)
    return results[:5]


def add_wiki_links(filepath: Path):
    """Add [[wiki-links]] to a note based on keyword groups."""
    text = filepath.read_text(encoding="utf-8", errors="ignore")
    if not text:
        return
    
    content = text
    # Add topic tags section if not present
    if "## 关联主题" not in text:
        tags_found = set()
        for topic, keywords in TOPIC_GROUPS.items():
            for kw in keywords:
                if kw.lower() in text.lower():
                    tags_found.add(topic)
                    break
        
        if tags_found:
            links = " ".join(f"[[{t}]]" for t in sorted(tags_found))
            content += f"\n\n## 关联主题\n{links}\n"
    
    # Add related notes section if not present (placeholder for batch processing)
    if "## 相关笔记" not in text:
        content += "\n<!-- related_notes_auto -->\n"
    
    if content != text:
        filepath.write_text(content, encoding="utf-8")
        return True
    return False


def create_daily_index(date_str: Optional[str] = None):
    """Create or update a daily summary index page."""
    if date_str is None:
        date_str = date.today().isoformat()
    
    vault = Path(VAULT_PATH)
    index_path = vault / f"{date_str} 日报.md"
    
    # Find all notes from this date
    date_notes = []
    for fpath in vault.rglob("*.md"):
        if index_path.name in str(fpath):
            continue
        if date_str in str(fpath):
            try:
                text = fpath.read_text(encoding="utf-8", errors="ignore")
                date_notes.append({
                    "path": str(fpath),
                    "name": fpath.stem,
                    "content": text[:200],
                    "modified": fpath.stat().st_mtime,
                })
            except:
                continue
    
    if not date_notes:
        return
    
    # Build index
    content = f"---\ntitle: {date_str} 日报\ndate: {date_str}\ntags: [daily, index]\n---\n\n# {date_str} 日报\n\n"
    content += f"本日共 {len(date_notes)} 条笔记\n\n"
    
    for note in sorted(date_notes, key=lambda x: x["modified"]):
        content += f"- [[{note['name']}]]\n"
        content += f"  - {note['content'][:100].strip()}\n\n"
    
    # Add topic summary
    topics = defaultdict(int)
    for note in date_notes:
        for topic, keywords in TOPIC_GROUPS.items():
            for kw in keywords:
                if kw in note["content"]:
                    topics[topic] += 1
                    break
    
    if topics:
        content += "## 今日话题\n"
        for topic, count in sorted(topics.items(), key=lambda x: -x[1]):
            content += f"- [[{topic}]]: {count} 条\n"
    
    index_path.write_text(content, encoding="utf-8")
    logger.info("Daily index created: %s", index_path)
    return index_path


def create_topic_indexes():
    """Create or update topic index pages."""
    vault = Path(VAULT_PATH)
    
    # Collect all notes by topic
    topic_notes = defaultdict(list)
    
    for fpath in vault.rglob("*.md"):
        if fpath.stem in TOPIC_GROUPS or "日报" in fpath.stem or "索引" in fpath.stem:
            continue
        try:
            text = fpath.read_text(encoding="utf-8", errors="ignore")
            for topic, keywords in TOPIC_GROUPS.items():
                for kw in keywords:
                    if kw.lower() in text.lower():
                        rel_path = fpath.relative_to(vault)
                        topic_notes[topic].append({
                            "path": str(rel_path),
                            "name": fpath.stem,
                            "preview": text[:150].strip(),
                            "modified": fpath.stat().st_mtime,
                        })
                        break
        except:
            continue
    
    for topic, notes in topic_notes.items():
        if len(notes) < 2:
            continue
        
        topic_path = vault / "索引" / f"{topic}.md"
        topic_path.parent.mkdir(exist_ok=True)
        
        # Sort by modified time
        notes.sort(key=lambda x: x["modified"], reverse=True)
        
        content = f"---\ntitle: {topic}\ntags: [index, {topic}]\n---\n\n# [[{topic}]]\n\n共 {len(notes)} 条相关笔记\n\n"
        
        for note in notes[:30]:  # Max 30 per index
            content += f"- [[{note['name']}]]\n"
            content += f"  - {note['preview'][:100].strip()}\n\n"
        
        topic_path.write_text(content, encoding="utf-8")
        logger.info("Topic index created: %s (%d notes)", topic_path, len(notes))


def run_organization():
    """Run full organization pass on the vault."""
    vault = Path(VAULT_PATH)
    if not vault.exists():
        logger.warning("Vault not found: %s", vault)
        return
    
    logger.info("Starting Obsidian organization...")
    
    # Step 1: Collect all notes
    all_notes = []
    for fpath in vault.rglob("*.md"):
        try:
            text = fpath.read_text(encoding="utf-8", errors="ignore")
            all_notes.append({
                "path": str(fpath),
                "name": fpath.stem,
                "content": text,
                "modified": fpath.stat().st_mtime,
            })
        except:
            continue
    
    logger.info("Found %d notes", len(all_notes))
    
    # Step 2: Add wiki-links to each note
    linked = 0
    for note in all_notes:
        fpath = Path(note["path"])
        if add_wiki_links(fpath):
            linked += 1
    logger.info("Added wiki-links to %d notes", linked)
    
    # Step 3: Create daily index for today
    today = date.today().isoformat()
    create_daily_index(today)
    
    # Step 4: Create topic indexes
    create_topic_indexes()
    
    logger.info("Organization complete")


# ── Batch link related notes ──
def batch_link_related():
    """Find and add related notes sections to all notes."""
    vault = Path(VAULT_PATH)
    if not vault.exists():
        return
    
    # Collect all notes
    all_notes = []
    for fpath in vault.rglob("*.md"):
        try:
            text = fpath.read_text(encoding="utf-8", errors="ignore")
            all_notes.append({
                "path": str(fpath),
                "name": fpath.stem,
                "content": text,
                "modified": fpath.stat().st_mtime,
            })
        except:
            continue
    
    for note in all_notes:
        fpath = Path(note["path"])
        text = fpath.read_text(encoding="utf-8", errors="ignore")
        
        # Find related notes
        related = find_related_notes(fpath, all_notes, threshold=0.15)
        if not related:
            continue
        
        # Replace placeholder or add section
        placeholder = "<!-- related_notes_auto -->"
        if placeholder in text:
            section = "## 相关笔记\n"
            for r in related:
                section += f"- [[{r['name']}]] (相似度: {r['similarity']:.0%})\n"
            section += "\n" + placeholder
            
            new_text = text.replace(placeholder, section)
            if new_text != text:
                fpath.write_text(new_text, encoding="utf-8")
                logger.debug("Added related notes to %s", fpath.stem)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    run_organization()
    batch_link_related()
    print("Organization complete!")
