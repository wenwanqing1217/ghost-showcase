"""短剧平台配置"""

import json
from pathlib import Path
from typing import List, Dict

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator, field_validator

from mindflow_map.secrets import get_secret_provider


BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Initialize secret provider for fetching sensitive values
_secret_provider = get_secret_provider()


def _get_secret(name: str, default: str = "") -> str:
    """Get a secret value from the secret provider."""
    value = _secret_provider.get(name, default)
    return value if value is not None else default


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env" if _get_secret("SECRET_PROVIDER", "env") == "env" else None,
        extra="ignore",
    )

    # 应用配置
    app_name: str = "MindFlow Map"
    app_version: str = "0.1.0"
    debug: bool = False

    # 飞书协作通讯配置
    feishu_app_id: str = ""
    feishu_app_secret: str = ""
    feishu_verification_token: str = ""
    feishu_encrypt_key: str = ""

    # 微信公众平台配置
    wechat_app_id: str = ""
    wechat_app_secret: str = ""
    wechat_token: str = ""
    wechat_encoding_aes_key: str = ""

    # 百度地图配置
    baidu_map_auth_token: str = ""

    # AI 模型配置
    openai_api_key: str = ""
    openai_base_url: str = "https://api.deepseek.com/v1"  # DeepSeek 默认
    ai_model: str = "deepseek-chat"
    llm_timeout: float = 10.0
    llm_max_retries: int = 2
    llm_circuit_breaker_threshold: int = 5
    llm_circuit_breaker_recovery: float = 60.0

    # 多模型自动切换：当主模型调用失败时，按顺序尝试回退模型
    # JSON 数组字符串，每项格式：{"base_url": "...", "api_key": "...", "model": "..."}
    model_fallbacks: List[Dict[str, str]] = []

    @field_validator("model_fallbacks", mode="before")
    @classmethod
    def _parse_model_fallbacks(cls, value):
        """解析 MODEL_FALLBACKS，支持 JSON 字符串或已解析的列表。"""
        if isinstance(value, list):
            return value
        if not value:
            return []
        try:
            parsed = json.loads(value)
            return parsed if isinstance(parsed, list) else []
        except (json.JSONDecodeError, TypeError):
            return []

    # Alpha-ID 配置
    alpha_id_api_url: str = "http://localhost:8000"
    alpha_id_api_key: str = ""

    # 数据库配置（路径固定到项目 data/ 目录，避免从不同目录启动时散落）
    database_url: str = f"sqlite+aiosqlite:///{BASE_DIR / 'data' / 'mindflow_map.db'}"

    # Redis 配置
    redis_url: str = ""
    redis_enabled: bool = False

    # 限流配置
    rate_limit_window_seconds: int = 60
    rate_limit_max_per_window: int = 100

    # 抖音短剧配置
    douyin_username: str = ""
    douyin_password: str = ""

    # Shopify 配置
    shopify_shop_domain: str = ""
    shopify_access_token: str = ""

    # 短剧平台内容预审配置
    shortdramas_api_url: str = ""
    shortdramas_api_key: str = ""
    shortdramas_webhook_secret: str = ""

    # 演示模式
    demo_mode: bool = False

    @model_validator(mode="before")
    @classmethod
    def _load_secrets_from_provider(cls, data):
        """Load secrets from provider when not in local env mode."""
        if not isinstance(data, dict):
            return data
        
        provider_type = _get_secret("SECRET_PROVIDER", "env")
        if provider_type == "env":
            return data
        
        # Map of field names to environment variable names
        secret_fields = {
            "feishu_app_id": "FEISHU_APP_ID",
            "feishu_app_secret": "FEISHU_APP_SECRET",
            "feishu_verification_token": "FEISHU_VERIFICATION_TOKEN",
            "feishu_encrypt_key": "FEISHU_ENCRYPT_KEY",
            "wechat_app_id": "WECHAT_APP_ID",
            "wechat_app_secret": "WECHAT_APP_SECRET",
            "wechat_token": "WECHAT_TOKEN",
            "wechat_encoding_aes_key": "WECHAT_ENCODING_AES_KEY",
            "baidu_map_auth_token": "BAIDU_MAP_AUTH_TOKEN",
            "openai_api_key": "OPENAI_API_KEY",
            "alpha_id_api_key": "ALPHA_ID_API_KEY",
            "douyin_username": "DOUYIN_USERNAME",
            "douyin_password": "DOUYIN_PASSWORD",
            "shopify_shop_domain": "SHOPIFY_SHOP_DOMAIN",
            "shopify_access_token": "SHOPIFY_ACCESS_TOKEN",
            "shortdramas_api_url": "SHORTDRAMAS_API_URL",
            "shortdramas_api_key": "SHORTDRAMAS_API_KEY",
            "shortdramas_webhook_secret": "SHORTDRAMAS_WEBHOOK_SECRET",
        }
        
        for field_name, env_var in secret_fields.items():
            if field_name not in data or not data[field_name]:
                secret_value = _get_secret(env_var, "")
                if secret_value:
                    data[field_name] = secret_value
        
        return data


settings = Settings()
