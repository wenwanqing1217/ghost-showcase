"""飞书指令路由器测试 — 不依赖真实凭证/网络，仅测路由判定逻辑。

覆盖：帮助指令、前缀匹配、kv 参数解析、handler 异常降级、非指令回退闲聊。
"""

from __future__ import annotations

import pytest

from mindflow_map.api import feishu_commands as fc


class TestParseKvArgs:
    def test_basic_kv(self):
        args = fc._parse_kv_args("文案 商品=香薰 价格=59", "商品=香薰 价格=59")
        assert args == {"商品": "香薰", "价格": "59"}

    def test_value_with_spaces_until_next_key(self):
        args = fc._parse_kv_args("标题=hello world 内容=foo bar", "标题=hello world 内容=foo bar")
        assert args == {"标题": "hello world", "内容": "foo bar"}

    def test_quoted_value(self):
        args = fc._parse_kv_args("标题='hello world' 内容=\"foo bar\"", "标题='hello world' 内容=\"foo bar\"")
        assert args == {"标题": "hello world", "内容": "foo bar"}

    def test_empty_after(self):
        assert fc._parse_kv_args("文案", "") == {}


class TestRouteCommand:
    @pytest.mark.asyncio
    async def test_help_variants(self):
        for text in ("帮助", "help", "?", "？", "指令"):
            result = await fc.route_command(text)
            assert result.startswith("🎬 Ghost 渠道助手")

    @pytest.mark.asyncio
    async def test_empty_or_whitespace_returns_none(self):
        assert await fc.route_command("") is None
        assert await fc.route_command("   ") is None

    @pytest.mark.asyncio
    async def test_prefix_routes_to_handler_with_args(self, monkeypatch):
        async def fake_handler(args, after):
            return f"ok:{args.get('商品')}:{after}"

        monkeypatch.setitem(fc._COMMAND_PREFIXES, "文案", ("文案", fake_handler))
        result = await fc.route_command("文案 商品=香薰 价格=59")
        assert result == "ok:香薰:商品=香薰 价格=59"

    @pytest.mark.asyncio
    async def test_handler_exception_degrades_to_error_text(self, monkeypatch):
        async def bad_handler(args, after):
            raise RuntimeError("boom")

        monkeypatch.setitem(fc._COMMAND_PREFIXES, "测试", ("测试", bad_handler))
        result = await fc.route_command("测试 xx=1")
        assert "❌ 指令执行失败" in result

    @pytest.mark.asyncio
    async def test_unrecognized_text_returns_none(self, monkeypatch):
        # 清空注册表，避免真实 handler 触发网络调用
        monkeypatch.setattr(fc, "_COMMAND_PREFIXES", {})
        assert await fc.route_command("今天天气怎么样") is None


class TestRouteEndpoint:
    """/api/v1/webhook/feishu/route HTTP 端点 — feishu-bot 调用入口"""

    def test_non_command_returns_handled_false(self, monkeypatch):
        from fastapi.testclient import TestClient

        from mindflow_map.main import app

        monkeypatch.setattr(fc, "_COMMAND_PREFIXES", {})
        with TestClient(app) as client:
            resp = client.post("/api/v1/webhook/feishu/route", json={"text": "今天天气怎么样"})
        assert resp.status_code == 200
        assert resp.json() == {"handled": False}

    def test_help_command_returns_reply(self, monkeypatch):
        from fastapi.testclient import TestClient

        from mindflow_map.main import app

        monkeypatch.setattr(fc, "_COMMAND_PREFIXES", {})
        with TestClient(app) as client:
            resp = client.post("/api/v1/webhook/feishu/route", json={"text": "帮助"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["handled"] is True
        assert "渠道助手" in body["reply"]

    def test_invalid_json_returns_400(self):
        from fastapi.testclient import TestClient

        from mindflow_map.main import app

        with TestClient(app) as client:
            resp = client.post("/api/v1/webhook/feishu/route", content=b"not-json")
        assert resp.status_code == 400


class TestNaturalLanguageIntent:
    """自然语言意图识别（前缀未命中时兜底）"""

    def test_detect_copy_intent(self):
        intent = fc._detect_nl_intent("帮我写北欧风香薰的闲鱼文案")
        assert intent is not None
        assert intent[0] == "copy"
        assert intent[1]["_raw"] == "帮我写北欧风香薰的闲鱼文案"

    def test_detect_video_intent(self):
        intent = fc._detect_nl_intent("生成一个北欧香薰的种草视频")
        assert intent[0] == "video"

    def test_detect_douyin_intent(self):
        intent = fc._detect_nl_intent("把这个发到抖音")
        assert intent[0] == "douyin"

    def test_detect_shortdrama_intent(self):
        intent = fc._detect_nl_intent("帮我提交短剧")
        assert intent[0] == "shortdrama"

    def test_no_intent_returns_none(self):
        assert fc._detect_nl_intent("今天天气怎么样") is None

    def test_kv_params_kept(self):
        intent = fc._detect_nl_intent("写个文案 商品=香薰 价格=59")
        assert intent[0] == "copy"
        assert intent[1]["商品"] == "香薰"

    @pytest.mark.asyncio
    async def test_nl_routes_to_handler(self, monkeypatch):
        # 用桩替换真实 copy handler，避免触发网络调用
        async def fake(args):
            return f"copy:{args.get('_raw')}"

        monkeypatch.setitem(fc._NL_HANDLERS, "copy", fake)
        result = await fc.route_command("帮我写北欧风香薰的闲鱼文案")
        assert result == "copy:帮我写北欧风香薰的闲鱼文案"
