"""
Net-Agent API Routes — /v1/net/*
=====================================
All routes require JWT authentication (via get_current_user dependency).
All user-scoped routes enforce row-level isolation.
"""

from fastapi import APIRouter, Depends, HTTPException
from task_queue.task_manager import complete_task, enqueue_task, list_pending

from net_agent_common.adapter_meta.vendor_registry import get_adapter, list_vendors
from net_agent_common.auth.crypto import encrypt_credential, generate_user_salt
from net_agent_common.auth.permission import get_current_user
from net_agent_common.db.sqlite_store import get_connection, now
from net_agent_common.utils.logger import logger

router = APIRouter(prefix="/v1/net", tags=["net-agent"])


# ── router config (read-only info) ──────────────────────────

@router.get("/vendors")
async def get_vendors():
    """List all supported router brands."""
    return {"vendors": list_vendors()}


@router.post("/config/save")
async def save_config(
    vendor: str,
    lan_address: str,
    username: str,
    password: str,
    user_id: str = Depends(get_current_user),
):
    """
    Save (or update) router connection config for the current user.
    Credentials are AES-GCM encrypted before storage.
    """
    # Validate vendor exists
    try:
        get_adapter(vendor)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    salt = generate_user_salt()
    enc_user = encrypt_credential(username, salt)
    enc_pass = encrypt_credential(password, salt)

    import json
    with get_connection() as conn:
        existing = conn.execute(
            "SELECT id FROM user_router_config WHERE user_id = ?",
            (user_id,),
        ).fetchone()

        if existing:
            conn.execute(
                """UPDATE user_router_config
                   SET vendor=?, lan_address=?, encrypted_username=?,
                       encrypted_password=?, salt=?, updated_at=?
                   WHERE user_id=?""",
                (vendor, lan_address, json.dumps(enc_user),
                 json.dumps(enc_pass), salt, now(), user_id),
            )
            logger.info("Updated router config for user %s", user_id)
        else:
            conn.execute(
                """INSERT INTO user_router_config
                   (user_id, vendor, lan_address, encrypted_username,
                    encrypted_password, salt, created_at, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, vendor, lan_address, json.dumps(enc_user),
                 json.dumps(enc_pass), salt, now(), now()),
            )
            logger.info("Created router config for user %s", user_id)

    return {"status": "saved", "vendor": vendor}


@router.get("/config")
async def get_config(user_id: str = Depends(get_current_user)):
    """Get current user's router config (credentials NOT returned)."""
    with get_connection() as conn:
        row = conn.execute(
            """SELECT vendor, lan_address, created_at, updated_at
               FROM user_router_config WHERE user_id = ?""",
            (user_id,),
        ).fetchone()

    if not row:
        raise HTTPException(status_code=404, detail="No router config found")

    return {
        "vendor": row["vendor"],
        "lan_address": row["lan_address"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


# ── task queue (client-facing) ─────────────────────────────

@router.post("/action/{action}")
async def queue_action(
    action: str,
    body: dict = None,
    user_id: str = Depends(get_current_user),
):
    """
    Queue a router action for the local client to execute.
    Supported actions: reboot, refresh_status, scan_devices, set_channel, ban_mac
    """
    valid_actions = {"reboot", "refresh_status", "scan_devices", "set_channel", "ban_mac"}
    if action not in valid_actions:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown action '{action}'. Valid: {valid_actions}",
        )

    task_id = enqueue_task(user_id, action, body or {})
    logger.info("Queued action '%s' for user %s (task_id=%d)", action, user_id, task_id)
    return {"task_id": task_id, "status": "pending"}


@router.get("/tasks/pending")
async def get_pending_tasks(user_id: str = Depends(get_current_user)):
    """Local client polls this to get pending commands."""
    return {"tasks": list_pending(user_id)}


@router.post("/tasks/{task_id}/complete")
async def finish_task(
    task_id: int,
    success: bool,
    detail: str = "",
    user_id: str = Depends(get_current_user),
):
    """Local client reports task completion."""
    complete_task(task_id, success, detail)
    return {"status": "recorded"}


# ── metrics upload (client → server) ───────────────────────

@router.post("/metrics/upload")
async def upload_metrics(
    body: dict,
    user_id: str = Depends(get_current_user),
):
    """
    Receive network metrics from the local client and store them.
    Called periodically by net_client.upload_metrics().
    """
    import json

    required_fields = {"timestamp"}
    missing = required_fields - body.keys()
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing fields: {missing}")

    with get_connection() as conn:
        conn.execute(
            """INSERT INTO network_inspect_logs
               (user_id, timestamp, latency_ms, packet_loss_pct, jitter_ms,
                online_devices_count, network_score, raw_data)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                user_id,
                body["timestamp"],
                body.get("latency_ms", 0),
                body.get("packet_loss_pct", 0),
                body.get("jitter_ms", 0),
                body.get("online_devices_count", 0),
                body.get("network_score", 100),
                json.dumps(body),
            ),
        )
    logger.info("Metrics uploaded for user %s (score=%s)", user_id, body.get("network_score"))
    return {"status": "ok"}


# ── logs ────────────────────────────────────────────────────

@router.get("/logs/history")
async def get_history(
    limit: int = 50,
    user_id: str = Depends(get_current_user),
):
    """Get historical network inspection logs."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT timestamp, latency_ms, packet_loss_pct, jitter_ms,
                      online_devices_count, network_score, raw_data
               FROM network_inspect_logs
               WHERE user_id = ?
               ORDER BY timestamp DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()

    return {"logs": [dict(r) for r in rows]}


@router.get("/logs/audit")
async def get_audit_logs(
    limit: int = 50,
    user_id: str = Depends(get_current_user),
):
    """Get operation audit log (reboots, bans, channel switches)."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT action, trigger_type, result, detail, operated_at
               FROM operation_audit_logs
               WHERE user_id = ?
               ORDER BY operated_at DESC LIMIT ?""",
            (user_id, limit),
        ).fetchall()

    return {"logs": [dict(r) for r in rows]}
