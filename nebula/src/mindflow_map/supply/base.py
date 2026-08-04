"""Supply Source Adapter Framework — Nebula
=============================================
Extends Nebula's plugin system to support standardized supply source adapters.

Architecture:
  Each supply source (1688, CJ Dropshipping, Shoplazta, user custom) implements
  the SupplyAdapter interface. The SupplyRegistry manages discovery and routing.

Standardized Product Schema:
  All adapters normalize their source data into the common schema, enabling
  downstream consumers (automation engine, marketplace, independent store) to
  work with uniform data regardless of source.

Design principles:
  - Pluggable: new sources register via @supply_adapter decorator
  - Isolated: each adapter manages its own auth, rate limits, retries
  - Normalized: common schema eliminates downstream branching
  - Auditable: every fetch is logged with source, timestamp, result count
"""

from __future__ import annotations

import abc
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Type

logger = logging.getLogger(__name__)


# ── Standardized Product Schema ──


@dataclass
class StandardizedProduct:
    """Canonical product representation across all supply sources.

    Every adapter converts source-specific data into this schema.
    Downstream systems (铺货引擎, 集市, 独立站) only consume this.
    """
    # Identity
    source_id: str            # Source platform's product ID
    source_name: str          # Adapter name (e.g., '1688', 'cj_dropshipping')
    sku: str                  # Merchant SKU (if available)
    title: str
    description: str = ""
    category: str = ""        # Source category path

    # Pricing
    price: float = 0.0        # Base price in source currency
    currency: str = "USD"     # Source currency
    compare_price: float = 0.0  # MSRP / original price
    cost_price: float = 0.0   # Cost price (for margin calc)

    # Inventory
    inventory: int = 0
    inventory_updated_at: Optional[str] = None

    # Media
    images: List[str] = field(default_factory=list)
    video_url: str = ""

    # Logistics
    shipping_weight: float = 0.0  # kg
    shipping_dimensions: Dict[str, float] = field(default_factory=dict)  # {length, width, height} cm
    origin_country: str = ""
    estimated_delivery_days: int = 7

    # Source metadata
    source_url: str = ""      # Original product page URL
    supplier_name: str = ""
    supplier_rating: float = 0.0
    raw_data: Dict[str, Any] = field(default_factory=dict)  # Original source response

    # Platform tracking
    fetched_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    synced_at: Optional[str] = None


@dataclass
class StandardizedOrder:
    """Canonical order representation for fulfillment routing."""
    source_order_id: str
    source_name: str
    items: List[Dict[str, Any]]
    total_amount: float
    currency: str = "USD"
    customer: Dict[str, Any] = field(default_factory=dict)
    shipping_address: Dict[str, Any] = field(default_factory=dict)
    status: str = "pending"
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SupplyFetchResult:
    """Result of a fetch operation from a supply source."""
    success: bool
    products: List[StandardizedProduct] = field(default_factory=list)
    total_count: int = 0
    page: int = 1
    has_more: bool = False
    error: Optional[str] = None
    duration_ms: float = 0.0
    fetched_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# ── Base Adapter Interface ──


class SupplyAdapter(abc.ABC):
    """Abstract base class for all supply source adapters.

    Subclasses implement source-specific API calls and data normalization.
    The framework handles auth, caching, rate limiting, and audit logging.
    """

    # Adapter metadata (override in subclass)
    name: str = "base"                    # Adapter identifier
    display_name: str = "Base Adapter"    # Human-readable name
    version: str = "1.0.0"
    supported_operations: List[str] = field(default_factory=lambda: ["fetch_products"])
    auth_type: str = "api_key"            # api_key | oauth | none

    # Rate limiting defaults (override per adapter)
    rate_limit_rpm: int = 60             # Requests per minute
    rate_limit_rps: int = 10             # Requests per second

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self._request_timestamps: List[float] = []
        self._fetch_log: List[Dict[str, Any]] = []

    @abc.abstractmethod
    async def authenticate(self) -> bool:
        """Validate credentials and establish session.

        Returns True if authentication successful, False otherwise.
        """
        ...

    @abc.abstractmethod
    async def fetch_products(
        self,
        page: int = 1,
        page_size: int = 50,
        category: str = "",
        keyword: str = "",
    ) -> SupplyFetchResult:
        """Fetch products from the supply source.

        Args:
            page: Page number (1-indexed)
            page_size: Items per page
            category: Filter by category path
            keyword: Search keyword

        Returns:
            SupplyFetchResult with normalized products
        """
        ...

    @abc.abstractmethod
    async def fetch_product_detail(self, source_id: str) -> Optional[StandardizedProduct]:
        """Fetch single product details by source ID."""
        ...

    @abc.abstractmethod
    async def check_inventory(self, source_ids: List[str]) -> Dict[str, int]:
        """Check current inventory for multiple products.

        Returns: {source_id: inventory_count}
        """
        ...

    async def health_check(self) -> Dict[str, Any]:
        """Check if the supply source is reachable and authenticated.

        Default implementation: try authenticate.
        Override for source-specific health checks.
        """
        try:
            result = await self.authenticate()
            return {"healthy": result, "adapter": self.name, "checked_at": datetime.utcnow().isoformat()}
        except Exception as e:
            return {"healthy": False, "adapter": self.name, "error": str(e), "checked_at": datetime.utcnow().isoformat()}

    # ── Internal helpers ──

    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits. Returns True if allowed."""
        now = time.time()
        # Remove timestamps older than 1 minute
        self._request_timestamps = [t for t in self._request_timestamps if t > now - 60]
        return len(self._request_timestamps) < self.rate_limit_rpm

    def _record_request(self):
        """Record a request timestamp for rate limiting."""
        self._request_timestamps.append(time.time())
        # Keep only recent timestamps
        cutoff = time.time() - 60
        self._request_timestamps = [t for t in self._request_timestamps if t > cutoff]

    def _log_fetch(self, operation: str, result: SupplyFetchResult):
        """Log fetch operation for audit trail."""
        entry = {
            "operation": operation,
            "adapter": self.name,
            "success": result.success,
            "count": len(result.products),
            "duration_ms": result.duration_ms,
            "error": result.error,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self._fetch_log.append(entry)
        logger.info("[%s] %s: %d products in %.1fms", self.name, operation, len(result.products), result.duration_ms)

    def get_fetch_log(self) -> List[Dict[str, Any]]:
        """Return audit log of fetch operations."""
        return list(self._fetch_log)


# ── Adapter Registry ──


class SupplyRegistry:
    """Central registry for supply source adapters.

    Adapters register via @supply_adapter decorator or explicit registration.
    """

    def __init__(self):
        self._adapters: Dict[str, Type[SupplyAdapter]] = {}
        self._instances: Dict[str, SupplyAdapter] = {}

    def register(
        self,
        adapter_cls: Type[SupplyAdapter],
        name: str | None = None,
    ) -> Type[SupplyAdapter]:
        """Register an adapter class."""
        resolved_name = name or getattr(adapter_cls, "name", adapter_cls.__name__)
        self._adapters[resolved_name] = adapter_cls
        logger.info("Supply adapter registered: %s (%s)", resolved_name, adapter_cls.display_name)
        return adapter_cls

    def get(self, name: str) -> Optional[Type[SupplyAdapter]]:
        """Get adapter class by name."""
        return self._adapters.get(name)

    def list_adapters(self) -> List[Dict[str, str]]:
        """List all registered adapters with metadata."""
        return [
            {
                "name": cls.name,
                "display_name": cls.display_name,
                "version": cls.version,
                "operations": cls.supported_operations,
                "auth_type": cls.auth_type,
            }
            for cls in self._adapters.values()
        ]

    def create_instance(self, name: str, config: Dict[str, Any] = None) -> Optional[SupplyAdapter]:
        """Create an instance of a registered adapter."""
        cls = self._adapters.get(name)
        if cls is None:
            return None
        instance = cls(config=config)
        self._instances[name] = instance
        return instance

    def get_instance(self, name: str) -> Optional[SupplyAdapter]:
        """Get existing adapter instance or create new one."""
        if name in self._instances:
            return self._instances[name]
        return self.create_instance(name)

    def clear(self):
        """Remove all registered adapters."""
        self._adapters.clear()
        self._instances.clear()


def supply_adapter(
    name: str | None = None,
    display_name: str | None = None,
):
    """Decorator to register a SupplyAdapter subclass.

    Usage:
        @supply_adapter(name="1688", display_name="1688 批发")
        class Adapter1688(SupplyAdapter):
            ...
    """
    def decorator(cls: Type[SupplyAdapter]) -> Type[SupplyAdapter]:
        if name:
            cls.name = name
        if display_name:
            cls.display_name = display_name
        _global_supply_registry.register(cls, name=cls.name)
        return cls
    return decorator


# Global registry
_supply_registry = SupplyRegistry()


def get_supply_registry() -> SupplyRegistry:
    """Return the global supply registry."""
    return _supply_registry
