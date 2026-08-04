# Alpha-ID

数字身份层（L2）。端口 `8000`。

- DID + JWT 认证
- 用户注册/登录
- 双链记忆存储
- 风险引擎

## 启动

```bash
cd alphaid/projects
cp .env.example .env
pip install -e ".[mcp,fairy]"
uvicorn src.main:app --host 0.0.0.0 --port 8000
```

Docker Compose: `docker compose up alphaid`

## 环境变量

| 变量 | 默认值 | 说明 |
|:-----|:-------|:-----|
| `DATABASE_URL` | — | PostgreSQL 连接串 |
| `AID_ALLOWED_ORIGINS` | — | CORS 允许来源 |
