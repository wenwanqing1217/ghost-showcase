"""Platform event subscription tests for Feishu and WeChat."""

from __future__ import annotations

import hashlib
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

from mindflow_map.main import app
from mindflow_map.workflows.engine import WorkflowEngine

client = TestClient(app)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _set_mock_engine():
    """Replace the app's workflow engine with a mock and return it."""
    mock_engine = MagicMock(spec=WorkflowEngine)
    mock_engine.execute = AsyncMock(return_value={"handled": True})
    app.state.workflow_engine = mock_engine
    return mock_engine


def _reset_engine(original):
    if original is not None:
        app.state.workflow_engine = original
    elif hasattr(app.state, "workflow_engine"):
        delattr(app.state, "workflow_engine")


# ---------------------------------------------------------------------------
# Feishu event subscription
# ---------------------------------------------------------------------------


class TestFeishuCallback:
    """Feishu URL verification and event dispatch tests."""

    def test_url_verification_challenge(self):
        resp = client.post(
            "/api/v1/events/feishu",
            json={"type": "url_verification", "challenge": "abc123"},
        )
        assert resp.status_code == 200
        assert resp.json() == {"challenge": "abc123"}

    def test_unsupported_callback_type_returns_400(self):
        resp = client.post(
            "/api/v1/events/feishu",
            json={"type": "unknown", "event": {}},
        )
        assert resp.status_code == 400

    def test_message_event_dispatches_to_workflow_engine(self):
        original = getattr(app.state, "workflow_engine", None)
        try:
            mock_engine = _set_mock_engine()
            resp = client.post(
                "/api/v1/events/feishu",
                json={
                    "type": "event_callback",
                    "event": {
                        "uuid": "evt-1",
                        "type": "im.message.receive_v1",
                        "message": {"message_id": "m1", "chat_id": "c1", "content": "hello"},
                        "sender": {"sender_id": {"user_id": "u1"}},
                    },
                },
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["handled"] is True
            assert body["result"] == {"handled": True}
            mock_engine.execute.assert_called_once_with(text="hello", user_id="u1")
        finally:
            _reset_engine(original)

    def test_empty_text_event_is_skipped(self):
        original = getattr(app.state, "workflow_engine", None)
        try:
            mock_engine = _set_mock_engine()
            resp = client.post(
                "/api/v1/events/feishu",
                json={
                    "type": "event_callback",
                    "event": {
                        "uuid": "evt-2",
                        "type": "im.message.receive_v1",
                        "message": {"message_id": "m1", "chat_id": "c1", "content": ""},
                        "sender": {"sender_id": {"user_id": "u1"}},
                    },
                },
            )
            assert resp.status_code == 200
            body = resp.json()
            assert body["handled"] is True
            assert body["result"] == {"skipped": True, "reason": "empty_text"}
            mock_engine.execute.assert_not_called()
        finally:
            _reset_engine(original)

    def test_missing_workflow_engine_returns_500(self):
        original = getattr(app.state, "workflow_engine", None)
        try:
            if hasattr(app.state, "workflow_engine"):
                delattr(app.state, "workflow_engine")

            resp = client.post(
                "/api/v1/events/feishu",
                json={
                    "type": "event_callback",
                    "event": {
                        "uuid": "evt-3",
                        "type": "im.message.receive_v1",
                        "message": {"message_id": "m1", "chat_id": "c1", "content": "hello"},
                        "sender": {"sender_id": {"user_id": "u1"}},
                    },
                },
            )
            assert resp.status_code == 500
        finally:
            _reset_engine(original)


# ---------------------------------------------------------------------------
# WeChat event subscription
# ---------------------------------------------------------------------------


class TestWechatCallback:
    """WeChat verification and message handling tests."""

    def test_echostr_verification(self, monkeypatch):
        token = "testtoken12345678"
        timestamp = "123456"
        nonce = "nonce"
        params = [token, timestamp, nonce]
        params.sort()
        signature = hashlib.sha1("".join(params).encode("utf-8")).hexdigest()
        monkeypatch.setattr("mindflow_map.api.wechat.settings.wechat_token", token)

        resp = client.post(
            "/api/v1/events/wechat",
            params={"signature": signature, "timestamp": timestamp, "nonce": nonce, "echostr": "hello"},
        )
        assert resp.status_code == 200
        assert resp.text == "hello"

    def test_text_message_returns_xml_reply(self, monkeypatch):
        token = "testtoken12345678"
        timestamp = "1"
        nonce = "2"
        params = [token, timestamp, nonce]
        params.sort()
        signature = hashlib.sha1("".join(params).encode("utf-8")).hexdigest()
        monkeypatch.setattr("mindflow_map.api.wechat.settings.wechat_token", token)

        original = getattr(app.state, "workflow_engine", None)
        try:
            mock_engine = MagicMock(spec=WorkflowEngine)
            mock_engine.execute = AsyncMock(return_value="reply text")
            app.state.workflow_engine = mock_engine

            body = (
                b"<xml>"
                b"<ToUserName><![CDATA[toUser]]></ToUserName>"
                b"<FromUserName><![CDATA[fromUser]]></FromUserName>"
                b"<CreateTime>1234567890</CreateTime>"
                b"<MsgType><![CDATA[text]]></MsgType>"
                b"<Content><![CDATA[" + "你好".encode("utf-8") + b"]]></Content>"
                b"</xml>"
            )
            resp = client.post(
                "/api/v1/events/wechat",
                params={"signature": signature, "timestamp": timestamp, "nonce": nonce},
                content=body,
                headers={"Content-Type": "application/xml"},
            )
            assert resp.status_code == 200
            assert "xml" in resp.headers.get("content-type", "")
            assert "reply text" in resp.text
        finally:
            _reset_engine(original)

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
            "/api/v1/events/wechat",
            params={"signature": signature, "timestamp": timestamp, "nonce": nonce},
            content=body,
            headers={"Content-Type": "application/xml"},
        )
        assert resp.status_code == 200
        assert "只支持文字消息" in resp.text
