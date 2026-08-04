# Feishu Bot

飞书 WebSocket Bot（L1 感知层）。

- 飞书消息接收/发送
- 用户身份绑定
- Code Runner 沙箱

## 启动

```bash
cd ghost-main/feishu-bot
cp .env.example .env
pip install -r requirements.txt
python bot.py
```

Docker Compose: `docker compose up feishu-bot`

## 环境变量

| 变量 | 说明 |
|:-----|:-----|
| `FEISHU_APP_ID` | 飞书应用 ID |
| `FEISHU_APP_SECRET` | 飞书应用密钥 |
| `CODEX_MAX_CONCURRENT` | 最大并发任务数（默认 3） |
| `CODE_RUNNER_DIR` | 代码运行工作区路径 |
