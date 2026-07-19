"""短剧平台配置"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
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

    # Alpha-ID 配置
    alpha_id_api_url: str = "http://localhost:8000"
    alpha_id_api_key: str = ""

    # 数据库配置
    database_url: str = "sqlite+aiosqlite:///./mindflow_map.db"

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


settings = Settings()
