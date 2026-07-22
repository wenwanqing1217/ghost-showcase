"""配置校验测试"""

import pytest
from mindflow_map.config_validator import check_all, check_wechat, check_douyin, check_shopify, check_shortdramas


def test_check_wechat_when_configured(monkeypatch):
    monkeypatch.setattr("mindflow_map.config.settings.wechat_app_id", "id")
    monkeypatch.setattr("mindflow_map.config.settings.wechat_app_secret", "secret")
    monkeypatch.setattr("mindflow_map.config.settings.wechat_token", "token")

    result = check_wechat()
    assert result["configured"] is True
    assert result["platform"] == "wechat"
    assert result["missing"] == []


def test_check_wechat_when_missing(monkeypatch):
    monkeypatch.setattr("mindflow_map.config.settings.wechat_app_id", "")
    monkeypatch.setattr("mindflow_map.config.settings.wechat_app_secret", "")
    monkeypatch.setattr("mindflow_map.config.settings.wechat_token", "")

    result = check_wechat()
    assert result["configured"] is False
    assert "WECHAT_APP_ID" in result["missing"]


def test_check_douyin_when_configured(monkeypatch):
    monkeypatch.setattr("mindflow_map.config.settings.douyin_username", "user")
    monkeypatch.setattr("mindflow_map.config.settings.douyin_password", "pass")

    result = check_douyin()
    assert result["configured"] is True
    assert result["missing"] == []


def test_check_douyin_when_missing(monkeypatch):
    monkeypatch.setattr("mindflow_map.config.settings.douyin_username", "")
    monkeypatch.setattr("mindflow_map.config.settings.douyin_password", "")

    result = check_douyin()
    assert result["configured"] is False
    assert "DOUYIN_USERNAME" in result["missing"]


def test_check_shopify_when_configured(monkeypatch):
    monkeypatch.setattr("mindflow_map.config.settings.shopify_shop_domain", "example.myshopify.com")
    monkeypatch.setattr("mindflow_map.config.settings.shopify_access_token", "token")

    result = check_shopify()
    assert result["configured"] is True
    assert result["missing"] == []


def test_check_shopify_when_missing(monkeypatch):
    monkeypatch.setattr("mindflow_map.config.settings.shopify_shop_domain", "")
    monkeypatch.setattr("mindflow_map.config.settings.shopify_access_token", "")

    result = check_shopify()
    assert result["configured"] is False
    assert "SHOPIFY_SHOP_DOMAIN" in result["missing"]


def test_check_shortdramas_when_configured(monkeypatch):
    monkeypatch.setattr("mindflow_map.config.settings.shortdramas_api_url", "https://example.com")
    monkeypatch.setattr("mindflow_map.config.settings.shortdramas_api_key", "key")

    result = check_shortdramas()
    assert result["configured"] is True
    assert result["platform"] == "shortdramas"
    assert result["missing"] == []


def test_check_shortdramas_when_missing(monkeypatch):
    monkeypatch.setattr("mindflow_map.config.settings.shortdramas_api_url", "")
    monkeypatch.setattr("mindflow_map.config.settings.shortdramas_api_key", "")

    result = check_shortdramas()
    assert result["configured"] is False
    assert "SHORTDRAMAS_API_URL" in result["missing"]


def test_check_all_returns_all_platforms(monkeypatch):
    monkeypatch.setattr("mindflow_map.config.settings.wechat_app_id", "")
    monkeypatch.setattr("mindflow_map.config.settings.wechat_app_secret", "")
    monkeypatch.setattr("mindflow_map.config.settings.wechat_token", "")
    monkeypatch.setattr("mindflow_map.config.settings.douyin_username", "")
    monkeypatch.setattr("mindflow_map.config.settings.douyin_password", "")
    monkeypatch.setattr("mindflow_map.config.settings.shopify_shop_domain", "")
    monkeypatch.setattr("mindflow_map.config.settings.shopify_access_token", "")
    monkeypatch.setattr("mindflow_map.config.settings.shortdramas_api_url", "")
    monkeypatch.setattr("mindflow_map.config.settings.shortdramas_api_key", "")

    result = check_all()
    assert "wechat" in result
    assert "douyin" in result
    assert "shopify" in result
    assert "shortdramas" in result
    assert all(not v["configured"] for v in result.values())
