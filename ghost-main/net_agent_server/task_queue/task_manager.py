"""
Task Queue — server → client command pipeline.
===============================================
The server writes tasks here; the local client polls and executes them.
This decouples the HTTP request (fast) from the actual router operation (slow, local).
"""

import json
from typing import Optional

from net_agent_common.db.sqlite_store import get_connection, now


def enqueue_task(user_id: str, task_type: str, body: dict = None) -> int:
    """Add a task to the queue. Returns the task id."""
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT INTO user_task_queue (user_id, task_type, task_body, status, created_at)
               VALUES (?, ?, ?, 'pending', ?)""",
            (user_id, task_type, json.dumps(body or {}), now()),
        )
        return cur.lastrowid


def claim_next_task(user_id: str) -> Optional[dict]:
    """
    Claim the next pending task for a user atomically.
    Returns None if no pending tasks.

    Uses a single UPDATE with sub-SELECT to avoid the SELECT-then-UPDATE
    race condition where multiple clients could claim the same task.
    """
    with get_connection() as conn:
        # 原子操作：UPDATE 带子查询 WHERE，一行完成 claim
        # SQLite 不支持 UPDATE ... RETURNING，用 total_changes 判断是否命中
        now_ts = now()
        conn.execute(
            """UPDATE user_task_queue
               SET status = 'claimed', claimed_at = ?
               WHERE id = (
                   SELECT id FROM user_task_queue
                   WHERE user_id = ? AND status = 'pending'
                   ORDER BY created_at ASC LIMIT 1
               )""",
            (now_ts, user_id),
        )
        if conn.total_changes == 0:
            return None
        # 读取刚 claim 的任务
        row = conn.execute(
            """SELECT id, task_type, task_body, created_at FROM user_task_queue
               WHERE user_id = ? AND status = 'claimed'
               ORDER BY claimed_at DESC LIMIT 1""",
            (user_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "task_type": row["task_type"],
            "task_body": json.loads(row["task_body"]) if row["task_body"] else {},
            "created_at": row["created_at"],
        }


def complete_task(task_id: int, success: bool, detail: str = "") -> None:
    """Mark a task as done or failed."""
    with get_connection() as conn:
        conn.execute(
            """UPDATE user_task_queue
               SET status = ?, completed_at = ?
               WHERE id = ?""",
            ("done" if success else "failed", now(), task_id),
        )


def list_pending(user_id: str) -> list[dict]:
    """List all pending tasks for a user."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT id, task_type, task_body, created_at FROM user_task_queue
               WHERE user_id = ? AND status = 'pending'
               ORDER BY created_at ASC""",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]
