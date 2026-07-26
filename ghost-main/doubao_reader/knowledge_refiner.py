"""
Knowledge Refiner — clean, dedup, and tag raw Doubao memories
===============================================================
Runs AFTER capture, BEFORE Obsidian write.
Zero LLM tokens — pure rule-based NLP.

Pipeline:
  1. Dedup by text similarity (fuzzy hash)
  2. Remove noise (system messages, too-short, repeated patterns)
  3. Auto-tag by content keywords
  4. Extract key info snippets
"""

import re
import hashlib
import logging
from typing import List, Dict, Any, Set
from datetime import datetime

logger = logging.getLogger("knowledge_refiner")

# ── Noise patterns to filter out ──
NOISE_PATTERNS = [
    r"^\s*$",
    r"^\d{1,3}\s*$",
    r"^(加载|发送|输入|撤回|复制|举报|点赞|点踩|分享|转发|删除|编辑)",
    r"^(http|https|www)\.",
    r"^(\[{1,3}|\{{1,3}|\({1,3})",
    r"^(好的|嗯|哦|啊|是|对|行|可以|ok|好)$",
    r"^.{1,3}$",  # too short
    r"^(New Chat|New conversation|Search|Settings|History|Help|Log out|Sign in|Sign up)",  # English UI
    r"^(Ctrl|Shift|Alt|Cmd|Command|Option)",  # Keyboard shortcuts
    r"^[A-Z][a-z]+ [A-Z][a-z]+$",  # English name lines
    r"^(Model|Mode|Theme|Language|Account|Profile)",  # English settings
    r"^(系统消息|系统提示|notification)", 
]

# ── Keyword → Tag mapping ──
KEYWORD_TAGS = {
    "代码": ["code", "technical"],
    "bug": ["bug", "technical"],
    "报错": ["error", "technical"],
    "python": ["python", "code"],
    "javascript": ["javascript", "code"],
    "html": ["html", "web"],
    "css": ["css", "web"],
    "设计": ["design", "ux"],
    "架构": ["architecture", "design"],
    "需求": ["requirement", "product"],
    "项目": ["project"],
    "obsidian": ["obsidian", "knowledge"],
    "vitest": ["test", "code"],
    "测试": ["test", "qa"],
    "部署": ["deploy", "devops"],
    "docker": ["docker", "devops"],
    "飞书": ["feishu", "bot"],
    "bot": ["bot"],
    "api": ["api", "technical"],
    "数据库": ["database", "technical"],
    "sql": ["sql", "database"],
    "canvas": ["canvas"],
    "图谱": ["graph", "knowledge"],
    "知识": ["knowledge"],
    "记忆": ["memory", "knowledge"],
    "ghost": ["ghost", "system"],
    "alpha": ["alpha-id", "system"],
    "gateway": ["gateway", "system"],
}


def is_noise(text: str) -> bool:
    """Check if a text is noise that should be filtered out."""
    if not text or len(text.strip()) < 4:
        return True
    for pattern in NOISE_PATTERNS:
        if re.match(pattern, text.strip(), re.IGNORECASE):
            return True
    return False


def dedup_messages(messages: List[Dict]) -> List[Dict]:
    """Deduplicate messages by fuzzy content hash."""
    seen: Set[str] = set()
    result = []
    for msg in messages:
        content = msg.get("content", "").strip()
        if not content:
            continue
        # Use first 50 chars as dedup key (fuzzy)
        key = content[:50].lower()
        key_hash = hashlib.md5(key.encode()).hexdigest()
        if key_hash not in seen:
            seen.add(key_hash)
            result.append(msg)
    return result


def auto_tag(content: str) -> List[str]:
    """Auto-generate tags based on keyword matching."""
    tags = set()
    content_lower = content.lower()
    for keyword, tag_list in KEYWORD_TAGS.items():
        if keyword.lower() in content_lower:
            for tag in tag_list:
                tags.add(tag)
    # Always add a general tag
    if not tags:
        tags.add("general")
    return sorted(list(tags))


def extract_snippets(content: str, max_snippets: int = 3) -> List[str]:
    """Extract key info snippets from content."""
    snippets = []
    
    # Find sentences with key indicators
    indicators = [
        r"[^。！？\n]+(是|为|采用|基于|使用|需要|实现|提供|支持|包含|包括)[^。！？\n]+",
        r"[^。！？\n]+(设计|架构|方案|流程|方法|策略|计划)[^。！？\n]+",
        r"[^。！？\n]+(因为|所以|如果|虽然|但是|然而)[^。！？\n]+",
    ]
    
    for pattern in indicators:
        matches = re.findall(pattern, content)
        for m in matches:
            m = m.strip()
            if len(m) > 10 and m not in snippets:
                snippets.append(m)
                if len(snippets) >= max_snippets:
                    break
        if len(snippets) >= max_snippets:
            break
    
    return snippets


def refine_memory(memory: Dict[str, Any]) -> Dict[str, Any]:
    """Process a single memory entry: dedup, clean, tag."""
    content = memory.get("content", "")
    if not content:
        return memory
    
    # Clean content
    lines = content.split("\n")
    clean_lines = [l for l in lines if not is_noise(l)]
    cleaned = "\n".join(clean_lines).strip()
    
    if not cleaned:
        return memory
    
    # Auto-tag
    tags = memory.get("tags", [])
    if isinstance(tags, str):
        tags = [tags]
    auto_tags = auto_tag(cleaned)
    all_tags = list(set(tags + auto_tags))
    
    # Extract snippets
    snippets = extract_snippets(cleaned)
    
    # If content is too long, keep first 500 chars as summary
    summary = cleaned
    if len(cleaned) > 500:
        summary = cleaned[:500] + "..."
    
    memory["content"] = summary
    memory["original_length"] = len(content)
    memory["tags"] = all_tags
    memory["snippets"] = snippets
    memory["refined_at"] = datetime.now().isoformat()
    
    return memory


def refine_conversation(metadata: Dict, messages: List[Dict]) -> List[Dict]:
    """Process conversation messages: dedup, filter noise, tag."""
    # Step 1: Dedup
    deduped = dedup_messages(messages)
    
    # Step 2: Filter noise
    cleaned = [m for m in deduped if not is_noise(m.get("content", ""))]
    
    # Step 3: Auto-tag each message
    for msg in cleaned:
        tags = auto_tag(msg.get("content", ""))
        msg["tags"] = tags
    
    return cleaned


# Quick test
if __name__ == "__main__":
    test_msg = "我需要设计一个Ghost系统的知识图谱可视化架构，使用Canvas来实现无限白板效果，并且对接Obsidian的知识库"
    print("Tags:", auto_tag(test_msg))
    print("Snippets:", extract_snippets(test_msg))
    
    test_memory = {
        "content": test_msg,
        "tags": ["doubao"],
        "category": "doubao_chat",
    }
    result = refine_memory(test_memory)
    print("Refined tags:", result["tags"])
    print("Refined snippets:", result["snippets"])
