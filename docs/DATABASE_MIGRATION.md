# 数据库迁移指南：SQLite → PostgreSQL

## 概述

所有子项目已从 SQLite 迁移到 **PostgreSQL 16**，通过根目录 `docker-compose.yml` 统一编排。

```
┌─────────────────────────────────────┐
│         PostgreSQL 16 (db)          │
│         port 5432                   │
├───────────┬───────────┬─────────────┤
│ mindflow  │    ds     │  alpha_id   │
│   _map    │           │             │
└───────────┴───────────┴─────────────┘
```

## 快速开始

### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 中的 DB_PASSWORD（生产环境必须修改）
```

### 2. 启动全部服务

```bash
docker compose up -d
```

PostgreSQL 容器启动时会自动执行 `sql/init/01-databases.sql` 创建三个数据库。

### 3. 验证运行

```bash
# 检查数据库健康
docker compose exec db pg_isready -U ghost -d ghost

# 检查各服务
curl http://localhost:2002/health    # mindflow-map
curl http://localhost:3004/api/health # DS Dashboard
curl http://localhost:8000/health    # AID Alpha-ID
```

## 各项目配置

### mindflow-map (Python FastAPI)

| 配置项 | 值 |
|--------|-----|
| 驱动 | `postgresql+asyncpg` |
| URL | `postgresql+asyncpg://ghost:password@db:5432/mindflow_map` |
| 迁移 | Alembic（PostgreSQL 模式自动运行） |
| 双模式 | 自动检测 URL，SQLite 仍可用 |

**关键改动**：
- `memory/store.py` — 新增 PostgreSQL 支持（pool_pre_ping, pool_recycle）
- `models/session.py` — 已有双模式逻辑，无需修改

### DS Dashboard (Next.js + Prisma)

| 配置项 | 值 |
|--------|-----|
| 驱动 | Prisma Client |
| URL | `postgresql://ghost:password@db:5432/ds?schema=public` |
| 迁移 | `npx prisma migrate dev`（需重新执行） |

**迁移步骤**：
```bash
cd DS

# 1. 更新 provider 为 postgresql（已完成）
# 2. 删除旧 SQLite 迁移
rm -rf prisma/migrations

# 3. 创建新的 PostgreSQL 迁移
npx prisma migrate dev --name init

# 4. 生成客户端
npx prisma generate
```

### AID Alpha-ID (Python)

| 配置项 | 值 |
|--------|-----|
| 驱动 | `psycopg[binary,pool]>=3.2` |
| URL | `DATABASE_URL=postgresql://ghost:password@db:5432/alpha_id` |
| 选择逻辑 | `DATABASE_URL` 存在且以 `postgresql` 开头则用 Postgres |

**关键改动**：
- `src/core/storage_postgres.py` — 新增 PostgreSQL 存储后端
- `src/alpha_id/container.py` — 自动检测 `DATABASE_URL` 选择后端

**迁移已有数据**：
```bash
cd AID/projects
export DATABASE_URL=postgresql://ghost:password@localhost:5432/alpha_id
python scripts/migrate_to_postgres.py
```

## 环境变量参考

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DB_USER` | `ghost` | PostgreSQL 用户名 |
| `DB_PASSWORD` | `ghost_secret` | PostgreSQL 密码 |
| `DB_NAME` | `ghost` | 默认数据库名 |
| `DB_PORT` | `5432` | 暴露端口 |

## 回退到 SQLite

如需临时回退：

1. **mindflow-map**: 设置 `DATABASE_URL=sqlite+aiosqlite:///./mindflow_map.db`
2. **DS**: 改回 `provider = "sqlite"` + `DATABASE_URL=file:./dev.db`
3. **AID**: 删除 `DATABASE_URL` 环境变量或设置 `STORAGE_BACKEND=sqlite`

## 备份与恢复

```bash
# 备份全部数据库
docker compose exec db pg_dumpall -U ghost > backup.sql

# 备份单个数据库
docker compose exec db pg_dump -U ghost mindflow_map > mindflow_map_backup.sql

# 恢复
docker compose exec -T db psql -U ghost < backup.sql
```

## 监控

```bash
# 查看连接数
docker compose exec db psql -U ghost -c "SELECT count(*) FROM pg_stat_activity;"

# 查看表大小
docker compose exec db psql -U ghost -d mindflow_map -c "SELECT tablename, pg_size_pretty(pg_total_size(tablename::regclass)) FROM pg_tables WHERE schemaname='public' ORDER BY pg_total_size(tablename::regclass) DESC;"
```
