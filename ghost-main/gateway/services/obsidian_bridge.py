#!/usr/bin/env python3
"""
Obsidian Knowledge Bridge — Bidirectional Sync
=================================================
Bridges the Ghost platform with Obsidian vault for knowledge management.

Architecture:
  Platform → Obsidian: Structured knowledge cards (products, orders, insights)
  Obsidian → Platform: Operational knowledge (strategies, supplier notes, patterns)

Sync directions:
  1. Auto-capture: Platform events → Knowledge cards in Obsidian
  2. Manual sync: User can trigger full/partial sync
  3. Read-back: Platform reads Obsidian notes for AI decision-making

Knowledge card types:
  - product:insight — Product performance insights
  - order:analysis — Order pattern analysis
  - supply:intel — Supply source intelligence
  - strategy:note — Business strategy notes
  - supplier:profile — Supplier profiles and ratings
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ── Enums ──


class KnowledgeType(str, Enum):
    PRODUCT_INSIGHT = "product:insight"
    ORDER_ANALYSIS = "order:analysis"
    SUPPLY_INTEL = "supply:intel"
    STRATEGY_NOTE = "strategy:note"
    SUPPLIER_PROFILE = "supplier:profile"
    MARKET_TREND = "market:trend"
    OPERATION_LOG = "operation:log"
    AI_DECISION = "ai:decision"


class SyncDirection(str, Enum):
    PLATFORM_TO_OBSIDIAN = "platform→obsidian"
    OBSIDIAN_TO_PLATFORM = "obsidian→platform"
    BIDIRECTIONAL = "both"


class SyncStatus(str, Enum):
    PENDING = "pending"
    SYNCING = "syncing"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


# ── Data Models ──


@dataclass
class KnowledgeCard:
    """A structured knowledge card in Obsidian."""
    id: str
    type: KnowledgeType
    title: str
    content: str
    tags: List[str] = field(default_factory=list)
    source: str = "platform"
    source_id: str = ""  # Original entity ID (product_id, order_id, etc.)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    file_path: str = ""

    def to_markdown(self) -> str:
        """Convert to Obsidian markdown with frontmatter."""
        tags_str = "\n  - ".join(self.tags) if self.tags else ""
        metadata_json = json.dumps(self.metadata, ensure_ascii=False, indent=2) if self.metadata else ""

        md = f"""---
id: {self.id}
type: {self.type.value}
source: {self.source}
source_id: {self.source_id}
created_at: {self.created_at}
updated_at: {self.updated_at}
tags:
  - {tags_str}
---

# {self.title}

{self.content}

"""
        if metadata_json:
            md += f"## Metadata\n```json\n{metadata_json}\n```\n"

        return md

    @classmethod
    def from_markdown(cls, file_path: str, text: str) -> Optional[KnowledgeCard]:
        """Parse a knowledge card from Obsidian markdown."""
        if not text.startswith("---"):
            return None

        end_idx = text.find("---", 3)
        if end_idx <= 0:
            return None

        frontmatter = text[3:end_idx]
        content = text[end_idx + 3:].strip()

        metadata = {}
        tags = []
        card_id = ""
        card_type = KnowledgeType.STRATEGY_NOTE
        source = "obsidian"
        source_id = ""
        created_at = ""
        updated_at = ""

        for line in frontmatter.split("\n"):
            line = line.strip()
            if line.startswith("id:"):
                card_id = line.split(":", 1)[1].strip()
            elif line.startswith("type:"):
                try:
                    card_type = KnowledgeType(line.split(":", 1)[1].strip())
                except ValueError:
                    pass
            elif line.startswith("source:"):
                source = line.split(":", 1)[1].strip()
            elif line.startswith("source_id:"):
                source_id = line.split(":", 1)[1].strip()
            elif line.startswith("created_at:"):
                created_at = line.split(":", 1)[1].strip()
            elif line.startswith("updated_at:"):
                updated_at = line.split(":", 1)[1].strip()
            elif line.startswith("  - "):
                tags.append(line[4:].strip())
            elif line.startswith("title:"):
                pass  # Title from content

        # Extract title from content
        title = "Untitled"
        if content.startswith("# "):
            title = content[2:].split("\n")[0].strip()

        return cls(
            id=card_id or str(uuid.uuid4())[:8],
            type=card_type,
            title=title,
            content=content,
            tags=tags,
            source=source,
            source_id=source_id,
            metadata=metadata,
            created_at=created_at or datetime.utcnow().isoformat(),
            updated_at=updated_at or datetime.utcnow().isoformat(),
            file_path=file_path,
        )


@dataclass
class SyncResult:
    """Result of a sync operation."""
    direction: SyncDirection
    status: SyncStatus
    total_cards: int = 0
    synced_cards: int = 0
    errors: List[str] = field(default_factory=list)
    started_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: str = ""


# ── Knowledge Bridge ──


class ObsidianKnowledgeBridge:
    """Bidirectional knowledge sync between Ghost platform and Obsidian vault."""

    def __init__(self, vault_path: str = None):
        self.vault_path = Path(vault_path) if vault_path else Path(self._default_vault_path())
        self._knowledge_dir = self.vault_path / "Ghost知识库" / "平台知识"
        self._sync_log: List[SyncResult] = []

        # Ensure directories exist
        self._knowledge_dir.mkdir(parents=True, exist_ok=True)

        # Sub-directories for each knowledge type
        self._type_dirs = {
            KnowledgeType.PRODUCT_INSIGHT: self._knowledge_dir / "商品洞察",
            KnowledgeType.ORDER_ANALYSIS: self._knowledge_dir / "订单分析",
            KnowledgeType.SUPPLY_INTEL: self._knowledge_dir / "货源情报",
            KnowledgeType.STRATEGY_NOTE: self._knowledge_dir / "策略笔记",
            KnowledgeType.SUPPLIER_PROFILE: self._knowledge_dir / "供应商档案",
            KnowledgeType.MARKET_TREND: self._knowledge_dir / "市场趋势",
            KnowledgeType.OPERATION_LOG: self._knowledge_dir / "运营日志",
            KnowledgeType.AI_DECISION: self._knowledge_dir / "AI决策",
        }
        for d in self._type_dirs.values():
            d.mkdir(parents=True, exist_ok=True)

    # ── Vault Path ──

    @staticmethod
    def _default_vault_path() -> str:
        return os.getenv("OBSIDIAN_VAULT", r"D:\Obsidian\Ghost知识库")

    # ── Write: Platform → Obsidian ──

    async def write_card(self, card: KnowledgeCard) -> str:
        """Write a knowledge card to Obsidian vault.

        Returns the file path where the card was written.
        """
        type_dir = self._type_dirs.get(card.type, self._knowledge_dir)
        type_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename: {type}_{id}.md
        filename = f"{card.type.value.replace(':', '_')}_{card.id}.md"
        file_path = type_dir / filename

        # Write atomically
        content = card.to_markdown()
        tmp_path = file_path.with_suffix(".md.tmp")
        tmp_path.write_text(content, encoding="utf-8")
        tmp_path.replace(file_path)

        card.file_path = str(file_path)
        logger.info("[Obsidian] Card written: %s → %s", card.title, file_path)
        return str(file_path)

    async def write_product_insight(
        self,
        product_id: str,
        title: str,
        content: str,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """Write a product insight card."""
        card = KnowledgeCard(
            id=str(uuid.uuid4())[:8],
            type=KnowledgeType.PRODUCT_INSIGHT,
            title=title,
            content=content,
            tags=tags or ["产品", "洞察"],
            source="platform",
            source_id=product_id,
            metadata=metadata or {},
        )
        return await self.write_card(card)

    async def write_order_analysis(
        self,
        order_id: str,
        title: str,
        content: str,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """Write an order analysis card."""
        card = KnowledgeCard(
            id=str(uuid.uuid4())[:8],
            type=KnowledgeType.ORDER_ANALYSIS,
            title=title,
            content=content,
            tags=tags or ["订单", "分析"],
            source="platform",
            source_id=order_id,
            metadata=metadata or {},
        )
        return await self.write_card(card)

    async def write_supply_intel(
        self,
        adapter_name: str,
        title: str,
        content: str,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """Write a supply intelligence card."""
        card = KnowledgeCard(
            id=str(uuid.uuid4())[:8],
            type=KnowledgeType.SUPPLY_INTEL,
            title=title,
            content=content,
            tags=tags or ["货源", "情报"],
            source="platform",
            source_id=adapter_name,
            metadata=metadata or {},
        )
        return await self.write_card(card)

    async def write_supplier_profile(
        self,
        supplier_name: str,
        title: str,
        content: str,
        rating: float = 0.0,
        tags: List[str] = None,
    ) -> str:
        """Write a supplier profile card."""
        card = KnowledgeCard(
            id=str(uuid.uuid4())[:8],
            type=KnowledgeType.SUPPLIER_PROFILE,
            title=title,
            content=content,
            tags=tags or ["供应商"],
            source="platform",
            source_id=supplier_name,
            metadata={"rating": rating},
        )
        return await self.write_card(card)

    async def write_operation_log(
        self,
        operation: str,
        title: str,
        content: str,
        tags: List[str] = None,
    ) -> str:
        """Write an operation log card."""
        card = KnowledgeCard(
            id=str(uuid.uuid4())[:8],
            type=KnowledgeType.OPERATION_LOG,
            title=title,
            content=content,
            tags=tags or ["运营", "日志"],
            source="platform",
            metadata={"operation": operation},
        )
        return await self.write_card(card)

    # ── Read: Obsidian → Platform ──

    def read_cards(
        self,
        knowledge_type: Optional[KnowledgeType] = None,
        source: str = "obsidian",
        limit: int = 50,
    ) -> List[KnowledgeCard]:
        """Read knowledge cards from Obsidian vault.

        Args:
            knowledge_type: Filter by type (None = all)
            source: Filter by source ('obsidian' for user notes, 'platform' for auto-generated)
            limit: Max cards to return

        Returns:
            List of KnowledgeCard objects
        """
        cards = []
        search_dirs = [self._knowledge_dir]

        if knowledge_type and knowledge_type in self._type_dirs:
            search_dirs = [self._type_dirs[knowledge_type]]

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue

            for fpath in search_dir.rglob("*.md"):
                if len(cards) >= limit:
                    break

                try:
                    text = fpath.read_text(encoding="utf-8")
                    card = KnowledgeCard.from_markdown(str(fpath), text)
                    if card and (source is None or card.source == source):
                        cards.append(card)
                except Exception as e:
                    logger.warning("[Obsidian] Failed to read %s: %s", fpath, e)

        cards.sort(key=lambda c: c.updated_at, reverse=True)
        return cards[:limit]

    def read_strategy_notes(self, limit: int = 20) -> List[KnowledgeCard]:
        """Read business strategy notes from Obsidian."""
        return self.read_cards(
            knowledge_type=KnowledgeType.STRATEGY_NOTE,
            source="obsidian",
            limit=limit,
        )

    def read_supplier_profiles(self, limit: int = 20) -> List[KnowledgeCard]:
        """Read supplier profiles from Obsidian."""
        return self.read_cards(
            knowledge_type=KnowledgeType.SUPPLIER_PROFILE,
            source="obsidian",
            limit=limit,
        )

    def read_market_trends(self, limit: int = 20) -> List[KnowledgeCard]:
        """Read market trend notes from Obsidian."""
        return self.read_cards(
            knowledge_type=KnowledgeType.MARKET_TREND,
            source="obsidian",
            limit=limit,
        )

    def search_cards(self, keyword: str, limit: int = 20) -> List[KnowledgeCard]:
        """Search knowledge cards by keyword."""
        all_cards = self.read_cards(limit=200)
        keyword_lower = keyword.lower()

        results = []
        for card in all_cards:
            score = 0
            if keyword_lower in card.title.lower():
                score += 10
            if keyword_lower in card.content.lower():
                score += 5
            if any(keyword_lower in tag.lower() for tag in card.tags):
                score += 3
            if score > 0:
                results.append((score, card))

        results.sort(key=lambda x: x[0], reverse=True)
        return [card for _, card in results[:limit]]

    # ── Sync ──

    async def sync_from_events(self, events: List[Dict[str, Any]]) -> SyncResult:
        """Sync platform events to Obsidian knowledge cards.

        Args:
            events: List of event data dicts from the event bus

        Returns:
            SyncResult with statistics
        """
        result = SyncResult(
            direction=SyncDirection.PLATFORM_TO_OBSIDIAN,
            status=SyncStatus.SYNCING,
        )

        for event in events:
            try:
                event_type = event.get("type", "")
                data = event.get("data", {})

                if event_type == "order:paid":
                    await self._sync_order_paid(data)
                elif event_type == "order:fulfilled":
                    await self._sync_order_fulfilled(data)
                elif event_type == "supply:inventory:updated":
                    await self._sync_inventory_update(data)
                elif event_type == "fulfillment:task:failed":
                    await self._sync_fulfillment_failure(data)
                else:
                    continue

                result.synced_cards += 1
            except Exception as e:
                logger.error("[Obsidian] Sync error for event %s: %s", event.get("type"), e)
                result.errors.append(str(e))

        result.total_cards = len(events)
        result.status = SyncStatus.COMPLETED if not result.errors else SyncStatus.PARTIAL
        result.completed_at = datetime.utcnow().isoformat()
        self._sync_log.append(result)

        return result

    async def full_sync(self, direction: SyncDirection = SyncDirection.BIDIRECTIONAL) -> SyncResult:
        """Perform a full sync between platform and Obsidian.

        This is a heavy operation — use with care.
        """
        result = SyncResult(direction=direction, status=SyncStatus.SYNCING)
        start = time.time()

        try:
            if direction in (SyncDirection.PLATFORM_TO_OBSIDIAN, SyncDirection.BIDIRECTIONAL):
                # Platform → Obsidian: read recent operations from DB and create cards
                # (Requires database access — implemented by caller)
                pass

            if direction in (SyncDirection.OBSIDIAN_TO_PLATFORM, SyncDirection.BIDIRECTIONAL):
                # Obsidian → Platform: read strategy notes and supplier profiles
                strategies = self.read_strategy_notes(limit=50)
                suppliers = self.read_supplier_profiles(limit=50)
                result.synced_cards += len(strategies) + len(suppliers)

            result.status = SyncStatus.COMPLETED
        except Exception as e:
            result.status = SyncStatus.FAILED
            result.errors.append(str(e))

        result.completed_at = datetime.utcnow().isoformat()
        result.total_cards = result.synced_cards
        self._sync_log.append(result)

        logger.info(
            "[Obsidian] Full sync completed: %s cards in %.1fs",
            result.synced_cards,
            time.time() - start,
        )
        return result

    # ── Event Handlers ──

    async def _sync_order_paid(self, data: Dict[str, Any]):
        """Create knowledge card for paid order."""
        order_id = data.get("orderId", "unknown")
        amount = data.get("amount", 0)
        currency = data.get("currency", "USD")

        content = f"""## 订单信息
- **订单号**: {order_id}
- **金额**: {amount} {currency}
- **状态**: 已付款

## 分析
- 付款时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M')}
- 来源: {data.get('storeMode', 'unknown')}

## 备注
自动生成的订单付款知识卡片。"""

        await self.write_order_analysis(
            order_id=order_id,
            title=f"订单 {order_id} 付款分析",
            content=content,
            tags=["订单", "付款", "自动"],
            metadata=data,
        )

    async def _sync_order_fulfilled(self, data: Dict[str, Any]):
        """Create knowledge card for fulfilled order."""
        order_id = data.get("orderId", "unknown")
        tracking = data.get("trackingNumber", "")

        content = f"""## 履约信息
- **订单号**: {order_id}
- **物流单号**: {tracking}
- **状态**: 已发货

## 备注
自动生成的订单发货知识卡片。"""

        await self.write_order_analysis(
            order_id=order_id,
            title=f"订单 {order_id} 发货记录",
            content=content,
            tags=["订单", "发货", "物流"],
            metadata=data,
        )

    async def _sync_inventory_update(self, data: Dict[str, Any]):
        """Create knowledge card for inventory changes."""
        source_id = data.get("sourceId", "unknown")
        inventory = data.get("inventory", 0)

        content = f"""## 库存变化
- **商品ID**: {source_id}
- **当前库存**: {inventory}

## 备注
自动生成的库存变化知识卡片。"""

        await self.write_product_insight(
            product_id=source_id,
            title=f"库存变化 {source_id}",
            content=content,
            tags=["库存", "变化", "自动"],
            metadata=data,
        )

    async def _sync_fulfillment_failure(self, data: Dict[str, Any]):
        """Create knowledge card for fulfillment failures."""
        order_id = data.get("orderId", "unknown")
        error = data.get("error", "Unknown")

        content = f"""## 履约失败
- **订单号**: {order_id}
- **错误**: {error}

## 备注
自动生成的履约失败知识卡片，需要人工跟进。"""

        await self.write_operation_log(
            operation="fulfillment_failure",
            title=f"履约失败 {order_id}",
            content=content,
            tags=["履约", "失败", "异常"],
        )

    # ── Status & Health ──

    def get_status(self) -> Dict[str, Any]:
        """Get Obsidian bridge status."""
        vault_exists = self.vault_path.exists()
        file_count = 0
        if vault_exists:
            for f in self.vault_path.rglob("*.md"):
                file_count += 1

        return {
            "vault_path": str(self.vault_path),
            "vault_exists": vault_exists,
            "total_md_files": file_count,
            "knowledge_cards_dir": str(self._knowledge_dir),
            "sync_history_count": len(self._sync_log),
            "last_sync": self._sync_log[-1].completed_at if self._sync_log else None,
        }

    def get_sync_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent sync history."""
        history = []
        for result in self._sync_log[-limit:]:
            history.append({
                "direction": result.direction.value,
                "status": result.status.value,
                "total": result.total_cards,
                "synced": result.synced_cards,
                "errors": len(result.errors),
                "started_at": result.started_at,
                "completed_at": result.completed_at,
            })
        return history


# ── Singleton ──

_bridge_instance: Optional[ObsidianKnowledgeBridge] = None


def get_obsidian_bridge(vault_path: str = None) -> ObsidianKnowledgeBridge:
    """Get or create the global Obsidian bridge instance."""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = ObsidianKnowledgeBridge(vault_path)
    return _bridge_instance


def reset_obsidian_bridge():
    """Reset the global instance (for testing)."""
    global _bridge_instance
    _bridge_instance = None
