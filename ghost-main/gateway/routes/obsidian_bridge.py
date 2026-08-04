"""Obsidian Bridge Routes — /v1/obsidian/*
===========================================
REST API for Obsidian knowledge bridge operations.

Routes:
  GET  /v1/obsidian/status         — Vault status
  GET  /v1/obsidian/cards          — List knowledge cards
  GET  /v1/obsidian/cards/search   — Search cards by keyword
  GET  /v1/obsidian/cards/strategies — Read strategy notes
  GET  /v1/obsidian/cards/suppliers  — Read supplier profiles
  POST /v1/obsidian/cards          — Write a knowledge card
  POST /v1/obsidian/sync           — Trigger sync from events
  GET  /v1/obsidian/sync/history   — Get sync history
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request, Query
from pydantic import BaseModel, Field

from services.obsidian_bridge import (
    get_obsidian_bridge,
    KnowledgeCard,
    KnowledgeType,
    SyncDirection,
    SyncStatus,
)
from services.proxy import ok, fail

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/obsidian", tags=["obsidian"])


# ── Request Schemas ──


class WriteCardRequest(BaseModel):
    """Write a knowledge card to Obsidian."""
    type: str = Field(..., description="Knowledge type: product:insight, order:analysis, etc.")
    title: str = Field(..., description="Card title")
    content: str = Field(..., description="Card content (markdown)")
    tags: List[str] = Field(default_factory=list)
    source_id: str = Field("", description="Original entity ID")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SyncRequest(BaseModel):
    """Trigger sync operation."""
    direction: str = Field("both", description="Sync direction: platform→obsidian | obsidian→platform | both")
    events: List[Dict[str, Any]] = Field(default_factory=list)


# ── Status ──


@router.get("/status")
async def obsidian_status(request: Request):
    """Get Obsidian vault and bridge status."""
    try:
        bridge = get_obsidian_bridge()
        status = bridge.get_status()
        return ok(status, request)
    except Exception as e:
        return fail(str(e), 500, request)


# ── Read Cards ──


@router.get("/cards")
async def list_cards(
    request: Request,
    type: Optional[str] = Query(None, description="Filter by knowledge type"),
    source: Optional[str] = Query(None, description="Filter by source"),
    limit: int = Query(50, ge=1, le=200),
):
    """List knowledge cards from Obsidian vault."""
    try:
        bridge = get_obsidian_bridge()
        knowledge_type = None
        if type:
            try:
                knowledge_type = KnowledgeType(type)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid knowledge type: {type}")

        cards = bridge.read_cards(knowledge_type=knowledge_type, source=source, limit=limit)
        return ok({
            "cards": [
                {
                    "id": c.id,
                    "type": c.type.value,
                    "title": c.title,
                    "content": c.content[:200],
                    "tags": c.tags,
                    "source": c.source,
                    "source_id": c.source_id,
                    "updated_at": c.updated_at,
                    "file_path": c.file_path,
                }
                for c in cards
            ],
            "total": len(cards),
        }, request)
    except HTTPException:
        raise
    except Exception as e:
        return fail(str(e), 500, request)


@router.get("/cards/search")
async def search_cards(
    request: Request,
    q: str = Query(..., description="Search keyword"),
    limit: int = Query(20, ge=1, le=100),
):
    """Search knowledge cards by keyword."""
    try:
        bridge = get_obsidian_bridge()
        cards = bridge.search_cards(q, limit=limit)
        return ok({
            "query": q,
            "cards": [
                {
                    "id": c.id,
                    "type": c.type.value,
                    "title": c.title,
                    "content": c.content[:300],
                    "tags": c.tags,
                    "updated_at": c.updated_at,
                }
                for c in cards
            ],
            "total": len(cards),
        }, request)
    except Exception as e:
        return fail(str(e), 500, request)


@router.get("/cards/strategies")
async def list_strategies(request: Request, limit: int = Query(20, ge=1, le=100)):
    """List business strategy notes."""
    try:
        bridge = get_obsidian_bridge()
        cards = bridge.read_strategy_notes(limit=limit)
        return ok({
            "cards": [
                {
                    "id": c.id,
                    "title": c.title,
                    "content": c.content,
                    "tags": c.tags,
                    "updated_at": c.updated_at,
                }
                for c in cards
            ],
            "total": len(cards),
        }, request)
    except Exception as e:
        return fail(str(e), 500, request)


@router.get("/cards/suppliers")
async def list_suppliers(request: Request, limit: int = Query(20, ge=1, le=100)):
    """List supplier profiles."""
    try:
        bridge = get_obsidian_bridge()
        cards = bridge.read_supplier_profiles(limit=limit)
        return ok({
            "cards": [
                {
                    "id": c.id,
                    "title": c.title,
                    "content": c.content,
                    "tags": c.tags,
                    "metadata": c.metadata,
                    "updated_at": c.updated_at,
                }
                for c in cards
            ],
            "total": len(cards),
        }, request)
    except Exception as e:
        return fail(str(e), 500, request)


# ── Write Cards ──


@router.post("/cards")
async def write_card(request: Request, body: WriteCardRequest):
    """Write a knowledge card to Obsidian vault."""
    try:
        bridge = get_obsidian_bridge()
        card = KnowledgeCard(
            id=str(__import__('uuid').uuid4())[:8],
            type=KnowledgeType(body.type),
            title=body.title,
            content=body.content,
            tags=body.tags,
            source="api",
            source_id=body.source_id,
            metadata=body.metadata,
        )
        file_path = await bridge.write_card(card)
        return ok({"id": card.id, "file_path": file_path}, request)
    except ValueError as e:
        return fail(f"Invalid knowledge type: {e}", 400, request)
    except Exception as e:
        return fail(str(e), 500, request)


# ── Sync ──


@router.post("/sync")
async def trigger_sync(request: Request, body: SyncRequest):
    """Trigger knowledge sync between platform and Obsidian."""
    try:
        bridge = get_obsidian_bridge()

        if body.events:
            # Sync from specific events
            result = await bridge.sync_from_events(body.events)
        else:
            # Full sync
            direction = SyncDirection(body.direction) if body.direction != "both" else SyncDirection.BIDIRECTIONAL
            result = await bridge.full_sync(direction=direction)

        return ok({
            "direction": result.direction.value,
            "status": result.status.value,
            "total": result.total_cards,
            "synced": result.synced_cards,
            "errors": result.errors,
        }, request)
    except ValueError as e:
        return fail(str(e), 400, request)
    except Exception as e:
        return fail(str(e), 500, request)


@router.get("/sync/history")
async def sync_history(request: Request, limit: int = Query(20, ge=1, le=100)):
    """Get recent sync history."""
    try:
        bridge = get_obsidian_bridge()
        history = bridge.get_sync_history(limit=limit)
        return ok({"history": history}, request)
    except Exception as e:
        return fail(str(e), 500, request)
