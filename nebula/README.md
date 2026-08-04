# Nebula

工作流引擎（L3）。端口 `2002`。

- Python FastAPI
- PostgreSQL 持久化
- 审计日志

## 启动

```bash
cd nebula
cp .env.example .env
pip install -e ".[dev]"
uvicorn src.mindflow_map.main:app --host 0.0.0.0 --port 2002
```

Docker Compose: `docker compose up nebula`

## 环境变量

| 变量 | 说明 |
|:-----|:-----|
| `DATABASE_URL` | PostgreSQL 连接串 |
