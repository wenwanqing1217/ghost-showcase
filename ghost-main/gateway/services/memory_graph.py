"""Memory knowledge graph operations."""

import json
import logging
import os
import sqlite3
from typing import Any, Dict

logger = logging.getLogger("ghost-gateway")

# Category color mapping for graph visualization
CATEGORY_COLORS = {
    "system": "#22c55e",
    "profile_cursor": "#a78bfa",
    "design": "#f59e0b",
    "general": "#64748b",
}


# Default database paths to query — override via MEMORY_GRAPH_DB_PATHS (comma-separated)
def _default_db_paths() -> list:
    env = os.environ.get("MEMORY_GRAPH_DB_PATHS", "").strip()
    if env:
        return [p.strip() for p in env.split(",") if p.strip()]
    # 回退：项目内 alpha_id.db（相对于本文件向上回溯）
    _fallback = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        "alphaid",
        "projects",
        "src",
        "assets",
        "alpha_id.db",
    )
    return [os.path.abspath(_fallback)]


DEFAULT_DB_PATHS = _default_db_paths()


def load_memories(db_paths: list = None) -> Dict[str, Any]:
    """Load memories from SQLite databases."""
    if db_paths is None:
        db_paths = DEFAULT_DB_PATHS

    memories = {}
    for dbp in db_paths:
        if not os.path.exists(dbp):
            continue
        try:
            conn = sqlite3.connect(dbp)
            row = conn.execute(
                "SELECT data FROM collections WHERE collection_name='Alpha-001'"
            ).fetchone()
            if row:
                memories.update(json.loads(row[0]))
            conn.close()
        except Exception as e:
            logger.warning("DB error loading memories from %s: %s", dbp, e)

    return memories


def build_graph(memories: Dict[str, Any]) -> Dict[str, Any]:
    """Build nodes and edges from memories for d3.js visualization."""
    nodes = []
    edges = []
    seen_tags: Dict[str, str] = {}

    for mid, mem in memories.items():
        if not isinstance(mem, dict):
            continue
        content = str(mem.get("content", ""))[:60]
        category = str(mem.get("category", "general"))
        source = str(mem.get("source", "unknown"))
        tags = mem.get("tags", []) or []
        if not isinstance(tags, list):
            tags = []

        nodes.append(
            {
                "id": mid[:12],
                "label": content,
                "category": category,
                "source": source,
                "color": CATEGORY_COLORS.get(category, "#64748b"),
                "tags": tags,
            }
        )

        for tag in tags:
            if tag in seen_tags:
                edges.append(
                    {
                        "from": mid[:12],
                        "to": seen_tags[tag][:12],
                        "label": tag,
                    }
                )
            else:
                seen_tags[tag] = mid

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "memories": len(nodes),
            "connections": len(edges),
        },
    }


def get_memory_graph(db_paths: list = None) -> Dict[str, Any]:
    """Get complete memory knowledge graph."""
    memories = load_memories(db_paths)
    return build_graph(memories)
