"""微信公众号 API 测试"""

import hashlib
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from mindflow_map.api.wechat import (
    _build_xml,
    _check_signature,
    _parse_xml,
    get_wechat_access_token,
    invalidate_wechat_access_token,
)
from mindflow_map.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# 工具函数测试
# ---------------------------------------------------------------------------

class TestCheckSignature:
    """签名校验逻辑测试"""

    def test_valid_signature(self, monkeypatch):
        monkeypatch.setattr("mindflow_map.api.wechat.settings.wechat_token", "a1b2c3d4e5f67890")
        assert _check_signature("signature", "123456", "nonce") is False  # 大概率不匹配

    def test_signature_matches(self, monkeypatch):
        token = "a1b2c3d4e5f67890"
        timestamp = "123456"
        nonce = "nonce"
        params = [token, timestamp, nonce]
        params.sort()
        expected = hashlib.sha1("".join(params).encode("utf-8")).hexdigest()
        monkeypatch.setattr("mindflow_map.api.wechat.settings.wechat_token", token)
        assert _check_signature(expected, timestamp, nonce) is True

    def test_missing_token_raises_500(self, monkeypatch):
        monkeypatch.setattr("mindflow_map.api.wechat.settings.wechat_token", "")
        with pytest.raises(HTTPException) as exc_info:
            _check_signature("any", "1", "2")
        assert exc_info.value.status_code == 500

    def test_signature_mismatch(self, monkeypatch):
        monkeypatch.setattr("mindflow_map.api.wechat.settings.wechat_token", "a1b2c3d4e5f67890")
        assert _check_signature("bad_signature", "123456", "nonce") is False


class TestBuildXml:
    """XML 构造测试"""

    def test_build_xml_format(self):
        xml = _build_xml("from_user", "to_user", "hello")
        assert "<ToUserName><![CDATA[to_user]]></ToUserName>" in xml
        assert "<FromUserName><![CDATA[from_user]]></FromUserName>" in xml
        assert "<MsgType><![CDATA[text]]></MsgType>" in xml
        assert "<Content><![CDATA[hello]]></Content>" in xml

    def test_build_xml_escapes_cdata(self):
        xml = _build_xml("a", "b", "hello ]]> world")
        # CDATA 中的 ]]> 会被转义为 ]]]]><![CDATA[>，避免提前闭合 CDATA section
        assert "hello ]]]]><![CDATA[> world" in xml


class TestParseXml:
    """XML 解析测试"""

    def test_parse_text_message(self):
        body = (
            b"<xml>"
            b"<ToUserName><![CDATA[toUser]]></ToUserName>"
            b"<FromUserName><![CDATA[fromUser]]></FromUserName>"
            b"<CreateTime>1234567890</CreateTime>"
            b"<MsgType><![CDATA[text]]></MsgType>"
            b"<Content><![CDATA[hello]]></Content>"
            b"<MsgId>12345</MsgId>"
            b"</xml>"
        )
        msg = _parse_xml(body)
        assert msg.to_user == "toUser"
        assert msg.from_user == "fromUser"
        assert msg.create_time == 1234567890
        assert msg.msg_type == "text"
        assert msg.content == "hello"
        assert msg.msg_id == 12345

    def test_parse_missing_optional_fields(self):
        body = (
            b"<xml>"
            b"<ToUserName><![CDATA[toUser]]></ToUserName>"
            b"<FromUserName><![CDATA[fromUser]]></FromUserName>"
            b"<CreateTime>1234567890</CreateTime>"
            b"<MsgType><![CDATA[text]]></MsgType>"
            b"</xml>"
        )
        msg = _parse_xml(body)
        assert msg.content is None
        assert msg.msg_id is None


# ---------------------------------------------------------------------------
# HTTP 路由测试
# ---------------------------------------------------------------------------

class TestWechatVerify:
    """微信服务器验证路由测试"""

    def test_verify_success(self, monkeypatch):
        token = "testtoken12345678"
        timestamp = "123456"
        nonce = "nonce"
        params = [token, timestamp, nonce]
        params.sort()
        signature = hashlib.sha1("".join(params).encode("utf-8")).hexdigest()
        monkeypatch.setattr("mindflow_map.api.wechat.settings.wechat_token", token)

        resp = client.get(
            "/api/v1/wechat",
            params={"signature": signature, "timestamp": timestamp, "nonce": nonce, "echostr": "hello"},
        )
        assert resp.status_code == 200
        assert resp.text == "hello"

    def test_verify_invalid_signature(self, monkeypatch):
        monkeypatch.setattr("mindflow_map.api.wechat.settings.wechat_token", "testtoken12345678")
        resp = client.get(
            "/api/v1/wechat",
            params={"signature": "bad", "timestamp": "123", "nonce": "456", "echostr": "hello"},
        )
        assert resp.status_code == 403


class TestWechatMessage:
    """微信消息接收路由测试"""

    def test_text_message_returns_reply(self, monkeypatch):
        token = "testtoken12345678"
        timestamp = "1"
        nonce = "2"
        params = [token, timestamp, nonce]
        params.sort()
        signature = hashlib.sha1("".join(params).encode("utf-8")).hexdigest()
        monkeypatch.setattr("mindflow_map.api.wechat.settings.wechat_token", token)
        body = (
            b"<xml>"
            b"<ToUserName><![CDATA[toUser]]></ToUserName>"
            b"<FromUserName><![CDATA[fromUser]]></FromUserName>"
            b"<CreateTime>1234567890</CreateTime>"
            b"<MsgType><![CDATA[text]]></MsgType>"
            b"<Content><![CDATA[" + "你好".encode() + b"]]></Content>"
            b"</xml>"
        )
        resp = client.post(
            f"/api/v1/wechat?signature={signature}&timestamp={timestamp}&nonce={nonce}",
            content=body,
            headers={"Content-Type": "application/xml"},
        )
        assert resp.status_code == 200
        assert "xml" in resp.headers["content-type"]
        assert b"<Content>" in resp.content

    def test_non_text_message_returns_fallback(self, monkeypatch):
        token = "testtoken12345678"
        timestamp = "1"
        nonce = "2"
        params = [token, timestamp, nonce]
        params.sort()
        signature = hashlib.sha1("".join(params).encode("utf-8")).hexdigest()
        monkeypatch.setattr("mindflow_map.api.wechat.settings.wechat_token", token)
        body = (
            b"<xml>"
            b"<ToUserName><![CDATA[toUser]]></ToUserName>"
            b"<FromUserName><![CDATA[fromUser]]></FromUserName>"
            b"<CreateTime>1234567890</CreateTime>"
            b"<MsgType><![CDATA[image]]></MsgType>"
            b"<PicUrl><![CDATA[http://example.com/img.jpg]]></PicUrl>"
            b"</xml>"
        )
        resp = client.post(
            f"/api/v1/wechat?signature={signature}&timestamp={timestamp}&nonce={nonce}",
            content=body,
            headers={"Content-Type": "application/xml"},
        )
        assert resp.status_code == 200
        assert "只支持文字消息".encode() in resp.content


# ---------------------------------------------------------------------------
# Access Token 测试
# ---------------------------------------------------------------------------

class TestWechatAccessToken:
    """Access Token 缓存测试"""

    def test_invalidate_clears_cache(self):
        from mindflow_map.api.wechat import _ACCESS_TOKEN_CACHE, fresh_token_cache
        with fresh_token_cache():
            _ACCESS_TOKEN_CACHE["token"] = "cached_token"
            _ACCESS_TOKEN_CACHE["expire_at"] = 9999999999
            invalidate_wechat_access_token()
            assert _ACCESS_TOKEN_CACHE["token"] == ""
            assert _ACCESS_TOKEN_CACHE["expire_at"] == 0.0

    @patch("mindflow_map.api.wechat.httpx.AsyncClient")
    def test_get_access_token_success(self, mock_client_cls, monkeypatch):
        from mindflow_map.api.wechat import fresh_token_cache
        monkeypatch.setattr("mindflow_map.api.wechat.settings.wechat_app_id", "appid")
        monkeypatch.setattr("mindflow_map.api.wechat.settings.wechat_app_secret", "secret")
        with fresh_token_cache():
            invalidate_wechat_access_token()

        # AsyncMock 模拟 httpx.AsyncClient：get() 返回 Mock Response
        mock_response = Mock()
        mock_response.json.return_value = {"access_token": "new_token", "expires_in": 7200}
        mock_response.raise_for_status.return_value = None

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        # async with 需要 __aenter__ 返回 client 自身
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = False
        mock_client_cls.return_value = mock_client

        import asyncio
        token = asyncio.run(get_wechat_access_token())
        assert token == "new_token"
