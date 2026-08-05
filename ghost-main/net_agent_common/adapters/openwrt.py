"""
OpenWrtAdapter — OpenWrt / 软路由 adapter
==========================================
Uses ``aio-openwrt`` (async ubus client) to talk to OpenWrt's ubus bus.
No scraping, no SSH — calls the official OpenWrt RPC interface directly.

Requirements:
    pip install aio-openwrt

Usage::

    adapter = OpenWrtAdapter(host="192.168.1.1", username="root", password="xxx")
    async with adapter:
        info = await adapter.get_wan_info()
"""


from net_agent_common.adapter_meta.vendor_registry import register
from net_agent_common.adapters.base import (
    AdapterConnectionError,
    AdapterError,
    BaseRouterAdapter,
    LanDevice,
    NetworkQuality,
    RouterBasicInfo,
    WanInfo,
)


@register("openwrt")
class OpenWrtAdapter(BaseRouterAdapter):
    """OpenWrt adapter via ubus (aio-openwrt)."""

    vendor = "openwrt"

    def __init__(self, host: str, username: str, password: str, port: int = 80,
                 timeout: float = 10.0, use_https: bool = False):
        self.host = host
        self.username = username
        self.password = password
        self.port = port
        self.timeout = timeout
        self.use_https = use_https
        self._client = None  # aio_openwrt.OpenWrtClient

    # ── lifecycle ────────────────────────────────────────────

    async def _connect(self):
        try:
            from aio_openwrt import OpenWrtClient
            scheme = "https" if self.use_https else "http"
            self._client = OpenWrtClient(
                host=self.host,
                username=self.username,
                password=self.password,
                port=self.port,
                scheme=scheme,
                timeout=self.timeout,
            )
            # Validate credentials with a lightweight call
            await self._client.call("system", "board")
        except ImportError:
            raise AdapterError("aio-openwrt not installed: pip install aio-openwrt")
        except Exception as e:
            raise AdapterConnectionError(f"Cannot connect to OpenWrt at {self.host}: {e}")

    async def _disconnect(self):
        if self._client:
            await self._client.close()
            self._client = None

    # ── WAN info ─────────────────────────────────────────────

    async def get_wan_info(self) -> WanInfo:
        try:
            # Network interface status for wan
            iface = await self._client.call("network.interface.wan", "status")
            ipv4 = iface.get("ipv4-address", [{}])
            ipv6 = iface.get("ipv6-address", [{}])
            external_ip = ipv4[0].get("address", "") if ipv4 else (
                ipv6[0].get("address", "") if ipv6 else ""
            )
            is_up = iface.get("up", False)

            return WanInfo(
                is_connected=is_up,
                external_ip=external_ip,
                uptime_seconds=iface.get("uptime", 0),
            )
        except Exception as e:
            raise AdapterError(f"get_wan_info failed: {e}")

    # ── LAN devices ──────────────────────────────────────────

    async def get_lan_devices(self) -> list[LanDevice]:
        devices: list[LanDevice] = []
        try:
            # DHCP leases give us hostname + IP + MAC
            leases = await self._client.call("uci", "get", {"config": "dhcp"})
            # Fallback: use netifd / arp table
            if not leases:
                arp = await self._client.call("network.device", "status")
                for iface_name, iface_data in (arp or {}).items():
                    for lease in iface_data.get("leases", []):
                        devices.append(LanDevice(
                            mac=lease.get("mac", ""),
                            ip=lease.get("ip", ""),
                            hostname=lease.get("hostname", ""),
                            band="wired" if "eth" in iface_name else "",
                        ))
            else:
                # Parse UCI dhcp output
                for section in leases.get("values", {}).values():
                    if section.get("type", "") == "host":
                        devices.append(LanDevice(
                            mac=section.get("mac", ""),
                            ip=section.get("ip", ""),
                            hostname=section.get("name", ""),
                        ))
        except Exception as e:
            raise AdapterError(f"get_lan_devices failed: {e}")
        return devices

    # ── Network quality ──────────────────────────────────────

    async def get_network_quality(self) -> NetworkQuality:
        """Ping external DNS via the router itself (if available) or fall back."""
        try:
            # Try to run ping on router via ubus sys.exec
            result = await self._client.call("file", "exec", {
                "command": "ping",
                "params": ["-c", "3", "-W", "2", "223.5.5.5"],  # AliDNS
            })
            output = result.get("stdout", "")
            # Parse ping output for avg latency and loss
            latency = _parse_ping_avg(output)
            loss = _parse_ping_loss(output)
            return NetworkQuality(
                latency_ms=latency,
                packet_loss_pct=loss,
                score=_score(latency, loss),
            )
        except Exception:
            # If router-side ping unavailable, return empty
            return NetworkQuality()

    # ── Actions ──────────────────────────────────────────────

    async def reboot(self) -> bool:
        try:
            await self._client.call("system", "reboot")
            return True
        except Exception as e:
            raise AdapterError(f"reboot failed: {e}")

    async def set_wifi_channel(self, band: str, channel: int) -> bool:
        radio = "radio0" if band == "2.4G" else "radio1"
        try:
            await self._client.call("uci", "set", {
                "config": "wireless",
                "section": radio,
                "values": {"channel": str(channel)},
            })
            await self._client.call("uci", "commit", {"config": "wireless"})
            # Restart wifi to apply
            await self._client.call("system", "exec", {
                "command": "/etc/init.d/wireless",
                "params": ["restart"],
            })
            return True
        except Exception as e:
            raise AdapterError(f"set_wifi_channel failed: {e}")

    async def ban_mac(self, mac_addr: str) -> bool:
        """Add MAC to wireless deny list."""
        try:
            for band in ["radio0", "radio1"]:
                await self._client.call("uci", "add", {
                    "config": "wireless",
                    "type": "wifi-iface",
                    "name": f"ban_{mac_addr.replace(':', '')}",
                    "values": {
                        "macfilter": "deny",
                        "maclist": mac_addr,
                    },
                })
            await self._client.call("uci", "commit", {"config": "wireless"})
            return True
        except Exception as e:
            raise AdapterError(f"ban_mac failed: {e}")

    async def get_basic_info(self) -> RouterBasicInfo:
        try:
            board = await self._client.call("system", "board")
            return RouterBasicInfo(
                model=board.get("system", ""),
                firmware_version=board.get("release", {}).get("version", ""),
                mac=board.get("mac", ""),
            )
        except Exception as e:
            raise AdapterError(f"get_basic_info failed: {e}")


# ── helpers ──────────────────────────────────────────────────

def _parse_ping_avg(output: str) -> float:
    """Extract avg latency from ping output (Linux format)."""
    for line in output.splitlines():
        if "avg" in line and "/" in line:
            # rtt min/avg/max/mdev = 1.234/5.678/9.012/1.234 ms
            parts = line.split("=")[-1].strip().split("/")
            if len(parts) >= 2:
                return float(parts[1])
    return 0.0


def _parse_ping_loss(output: str) -> float:
    """Extract packet loss percentage from ping output."""
    for line in output.splitlines():
        if "packet loss" in line:
            # 3 packets transmitted, 2 received, 33% packet loss
            pct = line.split("%")[0].split()[-1]
            return float(pct)
    return 0.0


def _score(latency: float, loss: float) -> int:
    """Simple 0-100 health score."""
    score = 100
    if latency > 0:
        score -= min(50, int(latency / 2))
    score -= int(loss * 2)
    return max(0, min(100, score))
