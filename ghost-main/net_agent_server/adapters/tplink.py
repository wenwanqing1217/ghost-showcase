"""
TPLinkWebAdapter — TP-Link / 水星 / 大众家用路由器适配器
=========================================================
Most consumer routers (TP-Link, Mercury, Tenda) only expose a web admin panel.
This adapter logs in via HTTP POST and scrapes the status pages.

No external library needed — uses httpx (already in the project).

Usage::

    adapter = TPLinkWebAdapter(host="192.168.1.1", password="admin")
    async with adapter:
        devices = await adapter.get_lan_devices()
"""

import asyncio
import re
from typing import Optional

from adapters.base import (
    AdapterAuthError,
    AdapterConnectionError,
    AdapterError,
    BaseRouterAdapter,
    LanDevice,
    NetworkQuality,
    RouterBasicInfo,
    WanInfo,
)
from adapter_meta.vendor_registry import register


@register("tplink")
class TPLinkWebAdapter(BaseRouterAdapter):
    """TP-Link / Mercury adapter via web scraping (httpx)."""

    vendor = "tplink"

    def __init__(self, host: str, password: str, username: str = "admin",
                 timeout: float = 10.0, use_https: bool = False):
        self.host = host
        self.username = username
        self.password = password
        self.timeout = timeout
        self.use_https = use_https
        self._client = None       # httpx.AsyncClient
        self._token = None        # session token after login
        self._stok = None         # TP-Link specific session token

    # ── lifecycle ────────────────────────────────────────────

    async def _connect(self):
        import httpx
        scheme = "https" if self.use_https else "http"
        base_url = f"{scheme}://{self.host}"
        self._client = httpx.AsyncClient(base_url=base_url, timeout=self.timeout)

        try:
            # TP-Link login: POST data is password-encoded (simple XOR or base64)
            encoded_pw = _encode_tplink_password(self.password)
            resp = await self._client.post("/cgi-bin/luci/admin/login", data={
                "username": self.username,
                "password": encoded_pw,
            })
            # Extract stok from redirect URL or response
            self._stok = _extract_stok(resp)
            if not self._stok:
                raise AdapterAuthError("Login failed — invalid credentials")
        except AdapterAuthError:
            raise
        except Exception as e:
            raise AdapterConnectionError(f"Cannot reach TP-Link at {self.host}: {e}")

    async def _disconnect(self):
        if self._client:
            await self._client.aclose()
            self._client = None

    # ── WAN info ─────────────────────────────────────────────

    async def get_wan_info(self) -> WanInfo:
        try:
            data = await self._get("/cgi-bin/luci/admin/network/wan_status")
            return WanInfo(
                is_connected=data.get("up", False),
                external_ip=data.get("ip", ""),
                uptime_seconds=data.get("uptime", 0),
            )
        except Exception as e:
            raise AdapterError(f"get_wan_info failed: {e}")

    # ── LAN devices ──────────────────────────────────────────

    async def get_lan_devices(self) -> list[LanDevice]:
        try:
            data = await self._get("/cgi-bin/luci/admin/network/dhcp_leases")
            devices = []
            for entry in data.get("leases", []):
                devices.append(LanDevice(
                    mac=entry.get("mac", ""),
                    ip=entry.get("ip", ""),
                    hostname=entry.get("hostname", ""),
                ))
            return devices
        except Exception as e:
            raise AdapterError(f"get_lan_devices failed: {e}")

    # ── Network quality ──────────────────────────────────────

    async def get_network_quality(self) -> NetworkQuality:
        # TP-Link web panel does not expose ping — return empty, probe from client
        return NetworkQuality()

    # ── Actions ──────────────────────────────────────────────

    async def reboot(self) -> bool:
        try:
            await self._post("/cgi-bin/luci/admin/system/reboot", {"action": "reboot"})
            return True
        except Exception as e:
            raise AdapterError(f"reboot failed: {e}")

    async def set_wifi_channel(self, band: str, channel: int) -> bool:
        try:
            iface = "2.4G" if band == "2.4G" else "5G"
            await self._post("/cgi-bin/luci/admin/wireless/channel", {
                "band": iface,
                "channel": channel,
            })
            return True
        except Exception as e:
            raise AdapterError(f"set_wifi_channel failed: {e}")

    async def ban_mac(self, mac_addr: str) -> bool:
        try:
            await self._post("/cgi-bin/luci/admin/wireless/macfilter", {
                "action": "add",
                "mac": mac_addr,
            })
            return True
        except Exception as e:
            raise AdapterError(f"ban_mac failed: {e}")

    async def get_basic_info(self) -> RouterBasicInfo:
        try:
            data = await self._get("/cgi-bin/luci/admin/system/status")
            return RouterBasicInfo(
                model=data.get("model", ""),
                firmware_version=data.get("fw_version", ""),
                mac=data.get("mac", ""),
            )
        except Exception as e:
            raise AdapterError(f"get_basic_info failed: {e}")

    # ── internal helpers ─────────────────────────────────────

    async def _get(self, path: str) -> dict:
        """GET with auth token, return parsed JSON."""
        resp = await self._client.get(path, params={"stok": self._stok})
        return resp.json() if resp.status_code == 200 else {}

    async def _post(self, path: str, data: dict) -> dict:
        """POST with auth token, return parsed JSON."""
        resp = await self._client.post(path, data={**data, "stok": self._stok})
        return resp.json() if resp.status_code == 200 else {}


# ── helpers ──────────────────────────────────────────────────

def _encode_tplink_password(password: str) -> str:
    """
    TP-Link uses a simple encoding for the login password.
    Most modern TP-Link routers use base64 encoding.
    """
    import base64
    return base64.b64encode(password.encode()).decode()


def _extract_stok(resp) -> Optional[str]:
    """Extract session token from TP-Link login response."""
    # stok is usually in the redirect URL: /cgi-bin/luci/;stok=XXXX/admin/...
    if resp.status_code in (301, 302):
        location = resp.headers.get("location", "")
        match = re.search(r"stok=([a-f0-9]+)", location)
        if match:
            return match.group(1)
    # Or in JSON response body
    try:
        data = resp.json()
        return data.get("stok") or data.get("data", {}).get("stok")
    except Exception:
        return None
