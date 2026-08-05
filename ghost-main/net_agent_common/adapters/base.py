"""
BaseRouterAdapter — Abstract Base Class
========================================
Defines the unified interface that every router brand adapter must implement.
All methods are async to keep the service fully non-blocking.

Design notes:
  - Adapters hold their own connection state (host, credentials, session).
  - Callers should use `async with adapter:` for automatic connect/disconnect.
  - Every method raises AdapterError on failure so the upper layer can
    handle uniformly (retry, alert, fallback).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass

# ──────────────────────────────────────────────────────────────
# Data types
# ──────────────────────────────────────────────────────────────

@dataclass
class WanInfo:
    """WAN / internet-facing status."""
    is_connected: bool
    external_ip: str
    upload_mbps: float = 0.0
    download_mbps: float = 0.0
    isp: str = ""
    uptime_seconds: int = 0


@dataclass
class LanDevice:
    """A single device on the LAN."""
    mac: str
    ip: str
    hostname: str = ""
    band: str = ""          # "2.4G" / "5G" / "wired"
    is_known: bool = False  # whether user has marked it as recognised


@dataclass
class NetworkQuality:
    """Aggregated latency / loss / jitter snapshot."""
    latency_ms: float = 0.0
    packet_loss_pct: float = 0.0
    jitter_ms: float = 0.0
    score: int = 100         # 0-100 health score


@dataclass
class RouterBasicInfo:
    """Static router identification."""
    model: str = ""
    firmware_version: str = ""
    mac: str = ""


# ──────────────────────────────────────────────────────────────
# Exceptions
# ──────────────────────────────────────────────────────────────

class AdapterError(Exception):
    """Base exception for all adapter operations."""
    pass


class AdapterConnectionError(AdapterError):
    """Could not reach the router."""
    pass


class AdapterAuthError(AdapterError):
    """Credentials rejected."""
    pass


class AdapterTimeoutError(AdapterError):
    """Operation timed out."""
    pass


# ──────────────────────────────────────────────────────────────
# Abstract base
# ──────────────────────────────────────────────────────────────

class BaseRouterAdapter(ABC):
    """
    Subclass this for every router brand.

    Minimal implementation pattern::

        class MyRouterAdapter(BaseRouterAdapter):
            vendor = "mybrand"

            async def _connect(self):
                ...

            async def _disconnect(self):
                ...

            async def _get_wan_info(self) -> WanInfo:
                ...
    """

    # -- class-level metadata ----------------------------------
    vendor: str = ""          # must match key in vendor_registry

    # -- lifecycle ---------------------------------------------

    async def __aenter__(self) -> "BaseRouterAdapter":
        await self._connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self._disconnect()

    async def _connect(self) -> None:
        """Establish connection to router. Override in subclass."""
        pass

    async def _disconnect(self) -> None:
        """Tear down connection. Override in subclass."""
        pass

    # -- public interface (all async) --------------------------

    @abstractmethod
    async def get_wan_info(self) -> WanInfo:
        """Return WAN / internet-facing status."""

    @abstractmethod
    async def get_lan_devices(self) -> list[LanDevice]:
        """Return every device currently on the LAN."""

    @abstractmethod
    async def get_network_quality(self) -> NetworkQuality:
        """Return latency / loss / jitter snapshot."""

    @abstractmethod
    async def reboot(self) -> bool:
        """Reboot the router. Returns True if command accepted."""

    @abstractmethod
    async def set_wifi_channel(self, band: str, channel: int) -> bool:
        """
        Switch WiFi channel.
        band: "2.4G" | "5G"
        channel: channel number (valid range depends on band)
        """

    @abstractmethod
    async def ban_mac(self, mac_addr: str) -> bool:
        """Block a MAC address from connecting."""

    @abstractmethod
    async def get_basic_info(self) -> RouterBasicInfo:
        """Return model / firmware / MAC."""

    # -- convenience helpers -----------------------------------

    async def get_unkown_devices(self, known_macs: set[str]) -> list[LanDevice]:
        """Filter LAN devices to only those not in *known_macs*."""
        all_devices = await self.get_lan_devices()
        return [d for d in all_devices if d.mac not in known_macs]
