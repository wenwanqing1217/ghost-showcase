"""feishu-bot 配置集中管理

所有环境变量读取和常量定义在此，不再散落在各模块。
"""

import os


# ── 飞书配置 ──
FEISHU_APP_ID = os.environ.get("FEISHU_APP_ID", "")
FEISHU_APP_SECRET = os.environ.get("FEISHU_APP_SECRET", "")
CODEX_PATH = os.environ.get("CODEX_PATH", "atomcode")

# ── 任务队列路径 ──
TASK_QUEUE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "tasks.json"
)

# ── 限流配置 ──
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "20"))

# ── 外部服务 URL（Phase 2 改由 PlatformRouter 管理，此处保留兼容） ──
NEBULA_URL = os.environ.get("NEBULA_URL", "http://localhost:2002").rstrip("/")
GATEWAY_URL = os.environ.get("GATEWAY_URL", "http://localhost:18080").rstrip("/")

# ── 待确认发布的确认/取消词 ──
_PUBLISH_CONFIRM_WORDS = {
    "发布", "确认", "确认发布", "可以", "可以发布", "发", "发布吧", "发吧",
    "好", "好的", "对", "是的", "ok", "ok!", "OK", "发送",
}
_PUBLISH_CANCEL_WORDS = {
    "取消", "不要", "算了", "不用", "撤销", "不发了", "别发", "不用了",
}
