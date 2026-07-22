# Ghost 部署手册

## 当前状态

各项目已完成本地开发环境配置，可通过 `start-demo.bat` 或 Docker Compose 启动。

| 项目 | 本地运行 | Docker | 测试 | 备注 |
|------|----------|--------|------|------|
| mindflow-map | ✅ | ✅ | 221/221 通过 | 需 .env 或 DEMO_MODE=true |
| DS | ✅ | ✅ | 40/40 通过 | 需 DASH_USER/DASH_PASS |
| AID | ✅ | ✅ | 928/928 通过 | 需 AUTH_MASTER_KEY |
| MindFlow | ✅ | ✅ | 32/32 通过 | web(3000) + api(3001) |
| zcode-brain | ✅ | - | 42/42 通过 | 无 Docker，仅测试 |
| ai综艺 | ✅ | - | N/A | 前端 Demo，无 Docker |

## 本地启动

### 方式一：一键启动（Windows）
双击 `start-demo.bat`，按菜单选择项目。

### 方式二：命令行启动

```bash
# mindflow-map（端口 2002）
cd mindflow-map
pip install -e ".[dev]"
uvicorn mindflow_map.main:app --reload --port 2002

# DS（端口 3004）
cd DS
npm install
npm run dev

# AID（端口 8000）
cd AID/projects
pip install -e ".\ !"
# Windows: set AUTH_MASTER_KEY=your-key-here
# Linux/Mac: export AUTH_MASTER_KEY=your-key-here
uvicorn src.main:app --reload --port 8000
```

## Docker 部署

### 统一编排（推荐）

```bash
cd D:\MW
docker compose up -d
```

服务端口分配：
- mindflow-map: 2002
- ds: 3004
- aid: 8000

### 单独部署

各项目目录含独立 `Dockerfile` 和 `docker-compose.yml`：

```bash
# mindflow-map
cd mindflow-map && docker compose up -d

# DS
cd DS && docker compose up -d

# AID
cd AID/projects && docker compose up -d
```

### 环境变量配置

各项目需提供 `.env` 文件（参考 `.env.example`）：

| 项目 | 必需变量 |
|------|----------|
| mindflow-map | `OPENAI_API_KEY` (或 `DEMO_MODE=true`) |
| DS | `DASH_USER`, `DASH_PASS` (或 `DEMO_MODE=true`) |
| AID | `AUTH_MASTER_KEY` (必须，任意 32+ 字符) |

## 生产部署注意事项

### 数据库
- 默认使用 SQLite，适合本地开发和演示
- 生产环境建议替换为 PostgreSQL
- DS 的 Prisma schema 支持多 provider

### 认证 & HTTPS
- 生产部署需配置 HTTPS（Caddy 或 Nginx 反向代理）
- `Caddyfile` 提供了自动 TLS 配置模板
- 各项目认证密钥需替换为强随机值

### 环境变量
- 生产 `.env` 文件不得提交到 Git
- 使用 Docker secrets 或 K8s secrets 管理密钥
- 轮换所有开发期间暴露的密钥

### 端口分配

| 服务 | 本地端口 | Docker 端口 |
|------|----------|-------------|
| mindflow-map | 2002 | 2002 |
| DS | 3004 (单独运行 3000) | 3004 |
| AID | 8000 | 8000 |
| MindFlow Web | 3000 | 3000 |
| MindFlow API | 3001 | 3001 |
| ai综艺 | 5173 | 5173 |

## 健康检查

```bash
# 快速检查所有服务
python scripts/health_check.py

# 手动检查
curl http://localhost:2002/health
curl http://localhost:3004/api/health
curl http://localhost:8000/health
```

## 已知限制

- **无 CI/CD**：测试仅在本地运行，未配置 GitHub Actions 等流水线
- **跨服务通信**：AID 的 JWT 验证端点已就绪，但 mindflow-map/DS 尚未默认启用 JWT 验证
- **LLM 依赖**：AI 功能需配置 OpenAI 兼容 API Key
- **存储层**：JSON 文件存储（AID）和 SQLite 不适合高并发生产场景

## 故障排除

### mindflow-map 启动失败
- 检查 `.env` 是否存在或设置 `DEMO_MODE=true`
- 检查 `data/` 目录是否自动创建

### DS 认证失败
- 检查 `DASH_USER` 和 `DASH_PASS` 是否设置
- 登录后 Cookie 未生效？检查浏览器是否阻止第三方 Cookie

### AID AUTH_MASTER_KEY 缺失
- AID 拒绝启动如果 `AUTH_MASTER_KEY` 未设置
- 生成随机密钥：`python -c "import secrets; print(secrets.token_hex(32))"`
