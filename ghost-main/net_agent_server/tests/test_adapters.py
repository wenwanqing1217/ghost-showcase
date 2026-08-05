"""
Adapter 层测试：BaseRouterAdapter 帮助方法 + OpenWrtAdapter 生命周期。
不依赖真实设备。
"""

import pytest

from net_agent_common.adapters.base import AdapterError, LanDevice
from net_agent_common.adapters.openwrt import OpenWrtAdapter

# ── get_unkown_devices ──────────────────────────────────────────

class _FakeAdapter(OpenWrtAdapter):
    """只实现 get_lan_devices 的假适配器（复用基类过滤逻辑）。"""

    def __init__(self, devices):
        super().__init__(host="192.168.1.1", username="root", password="p")
        self._devices = devices

    async def get_lan_devices(self):
        return self._devices


class TestUnknownDevices:
    @pytest.mark.asyncio
    async def test_filters_known_macs(self):
        devices = [
            LanDevice(mac="AA:BB:1", ip="192.168.1.2", is_known=True),
            LanDevice(mac="AA:BB:2", ip="192.168.1.3", is_known=False),
            LanDevice(mac="AA:BB:3", ip="192.168.1.4", is_known=False),
        ]
        adapter = _FakeAdapter(devices)

        result = await adapter.get_unkown_devices({"AA:BB:1"})

        assert [d.mac for d in result] == ["AA:BB:2", "AA:BB:3"]

    @pytest.mark.asyncio
    async def test_known_all_returns_empty(self):
        adapter = _FakeAdapter([LanDevice(mac="AA:BB:1", ip="192.168.1.2")])
        assert await adapter.get_unkown_devices({"AA:BB:1"}) == []


# ── OpenWrtAdapter 生命周期 ─────────────────────────────────────

class TestOpenWrtLifecycle:
    @pytest.mark.asyncio
    async def test_connect_raises_adapter_error_without_aio_openwrt(self):
        """本机/CI 未安装 aio-openwrt 时，连接应给出明确 AdapterError 而非裸 ImportError。"""
        adapter = OpenWrtAdapter("192.168.1.1", "root", "p")
        with pytest.raises(AdapterError):
            async with adapter:
                pass

    def test_vendor_registered(self):
        from net_agent_common.adapter_meta.vendor_registry import get_adapter

        assert get_adapter("openwrt") is OpenWrtAdapter
