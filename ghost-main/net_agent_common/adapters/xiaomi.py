"""
XiaomiAdapter — 小米 / Redmi 路由器适配器
============================================
Uses ``python-xiaomi-miwifi`` (synchronous library).
Wraps all calls in ``asyncio.to_thread`` so the rest of the service stays async.

Requirements:
    pip install python-xiaomi-miwifi

Usage::

    adapter = XiaomiAdapter(host="192.168.31.1", password="xxx")
    async with adapter:
        devices = await adapter.get_lan_devices()
"""

import asyncio
from functools import partial
from typing import Optional

from net_agent_common.adapters.base import (
    AdapterConnectionError,
    AdapterError,
    BaseRouterAdapter,
    LanDevice,
    NetworkQuality,
    RouterBasicInfo,
    WanInfo,
)
from net_agent_common.adapter_meta.vendor_registry import register


@register("xiaomi")
class XiaomiAdapter(BaseRouterAdapter):
    """Xiaomi / Redmi router adapter via python-xiaomi-miwifi (sync → async wrapped)."""

    vendor = "xiaomi"

    def __init__(self, host: str, password: str, timeout: float = 10.0):
        self.host = host
        self.password = password
        self.timeout = timeout
        self._client = None  # miwifi.MiWiFi

    # ── lifecycle ────────────────────────────────────────────

    async def _connect(self):
        try:
            from miwifi import MiWiFi
            self._client = MiWiFi(host=self.host, password=self.password)
            # Validate connection
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._client.login)
        except ImportError:
            raise AdapterError("python-xiaomi-miwifi not installed: pip install python-xiaomi-miwifi")
        except Exception as e:
            raise AdapterConnectionError(f"Cannot connect to Xiaomi router at {self.host}: {e}")

    async def _disconnect(self):
        self._client = None

    # ── WAN info ─────────────────────────────────────────────

    async def get_wan_info(self) -> WanInfo:
        try:
            loop = asyncio.get_running_loop()
            status = await loop.run_in_executor(
                None, partial(self._client.status)
            )
            wan = status.get("wan", {}) if isinstance(status, dict) else {}
            return WanInfo(
                is_connected=wan.get("up", False),
                external_ip=wan.get("ip", ""),
                uptime_seconds=wan.get("uptime", 0),
            )
        except Exception as e:
            raise AdapterError(f"get_wan_info failed: {e}")

    # ── LAN devices ──────────────────────────────────────────

    async def get_lan_devices(self) -> list[LanDevice]:
        try:
            loop = asyncio.get_running_loop()
            devices_raw = await loop.run_in_executor(
                None, partial(self._client.device_list)
            )
            devices = []
            for d in (devices_raw or {}).get("list", []):
                devices.append(LanDevice(
                    mac=d.get("mac", ""),
                    ip=d.get("ip", ""),
                    hostname=d.get("name", ""),
                    band=d.get("type", ""),  # 2.4G / 5G / wired
                ))
            return devices
        except Exception as e:
            raise AdapterError(f"get_lan_devices failed: {e}")

    # ── Network quality ──────────────────────────────────────

    async def get_network_quality(self) -> NetworkQuality:
        """Xiaomi API does not expose ping directly — return empty, probe from client side."""
        # TODO: implement client-side ping fallback (aioping)
        return NetworkQuality()

    # ── Actions ──────────────────────────────────────────────

    async def reboot(self) -> bool:
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, self._client.reboot)
            return True
        except Exception as e:
            raise AdapterError(f"reboot failed: {e}")

    async def set_wifi_channel(self, band: str, channel: int) -> bool:
        try:
            loop = asyncio.get_running_loop()
            # Xiaomi miwifi lib does not expose channel set directly
            # Use the miwifi CLI-equivalent if available
            raise AdapterError("set_wifi_channel not yet implemented for Xiaomi")
        except AdapterError:
            raise
        except Exception as e:
            raise AdapterError(f"set_wifi_channel failed: {e}")

    async def ban_mac(self, mac_addr: str) -> bool:
        try:
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None, partial(self._client.block_device, mac_addr)
            )
            return True
        except Exception as e:
            raise AdapterError(f"ban_mac failed: {e}")

    async def get_basic_info(self) -> RouterBasicInfo:
        try:
            loop = asyncio.get_running_loop()
            info = await loop.run_in_executor(
                None, partial(self._client.miio_info)
            )
            return RouterBasicInfo(
                model=info.get("model", ""),
                firmware_version=info.get("fw_ver", ""),
                mac=info.get("mac", ""),
            )
        except Exception as e:
            raise AdapterError(f"get_basic_info failed: {e}")
