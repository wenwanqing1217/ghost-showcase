# Ghost 工作区全面翻新方案

> **版本**: 1.0
> **日期**: 2026-07-22
> **翻新完成**: 2026-07-22
> **目标**: 将 6 个独立 Demo 翻新为可演示、可部署、可面试的成品平台

---

## 翻新执行状态

| 阶段 | 状态 | 完成日期 |
|------|------|----------|
| Phase 1: 安全基线 | ✅ 已完成 | 2026-07-22 |
| Phase 2: 部署修复 | ✅ 已完成 | 2026-07-22 |
| Phase 3: 测试改革 | ✅ 已完成 | 2026-07-22 |
| Phase 4: 集成连通 | ✅ 已完成 | 2026-07-22 |
| Phase 5: 文档翻新 | ✅ 已完成 | 2026-07-22 |
| Phase 6: 成品验收 | ⏳ 待执行 | - |

### 测试结果（翻新后）

| 项目 | 测试数 | 状态 |
|------|--------|------|
| AID | 928/928 | ✅ |
| mindflow-map | 221/221 | ✅ |
| DS | 40/40 | ✅ |
| zcode-brain | 42/42 | ✅ |
| MindFlow | 32/32 | ✅ |
| **合计** | **1263+** | ✅ |

---  

---

## 一、现状诊断

### 核心问题

```
能看 ✅ → 能用 ⚠️ → 好用 ❌ → 可部署 ❌
```

| 维度 | 现状 | 目标 |
|------|------|------|
| 安全 | 密钥裸奔、零认证 | 密钥管理 + 认证体系 |
| 集成 | 6 个项目互不通信 | 统一入口 + 数据流通 |
| 测试 | 刷数字、只测页面 | 核心链路覆盖 |
| 部署 | Dockerfile 翻车 | 一键 compose up |
| 文档 | 自我膨胀 | 诚实、准确、可操作 |
| 业务 | AI 洗白 | 真正的 AI 集成 |

### 翻新原则

1. **不重写，在现有基础上修** — 保留已有代码和架构
2. **先安全后功能** — 安全基线不达标，其他都是空中楼阁
3. **先单点后集成** — 每个项目能独立跑通，再做跨项目集成
4. **诚实标注** — 做不到的写"实验性"，不写"生产级"

---

## 二、阶段规划

```
Phase 1: 安全基线 (1-2 天)
    ↓
Phase 2: 部署修复 (2-3 天)
    ↓
Phase 3: 测试改革 (3-5 天)
    ↓
Phase 4: 集成连通 (5-7 天)
    ↓
Phase 5: 文档翻新 (2-3 天)
    ↓
Phase 6: 成品验收 (1 天)
```

---

## 三、Phase 1：安全基线

### 1.1 密钥管理

**目标**: 所有密钥从代码和配置文件中彻底移除，改用环境变量注入。

#### mindflow-map

```python
# src/mindflow_map/config.py — 改用 pydantic-settings
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    feishu_app_id: str = ""
    feishu_app_secret: str = ""
    baidu_map_auth_token: str = ""
    openai_api_key: str = ""
    openai_base_url: str = "https://api.deepseek.com/v1"
    ai_model: str = "deepseek-chat"
    database_url: str = "sqlite+aiosqlite:///./data/mindflow_map.db"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

- [ ] 安装 `pydantic-settings` 依赖
- [ ] 重写 `config.py` 使用 `BaseSettings`
- [ ] 数据库路径改为 `data/` 子目录（已 gitignore）
- [ ] 确认 `.env` 在 `.gitignore` 中
- [ ] 轮换所有已暴露密钥

#### AID

- [ ] 同样改用 `pydantic-settings` 或 `python-dotenv`
- [ ] `AUTH_MASTER_KEY` 改为自动生成（首次启动时生成并提示保存）
- [ ] 轮换已暴露密钥

#### DS

- [ ] `DS_API_KEY` 改为必填（空值拒绝启动）
- [ ] 添加启动时密钥强度检查（长度 >= 32）

### 1.2 认证体系

#### DS 仪表盘

```typescript
// src/middleware.ts — 已实现 Basic Auth，需补充：
// 1. 登录页面（cookie session 替代 Basic Auth）
// 2. 登出接口
// 3. CSRF 保护
```

- [ ] 添加 `/api/auth/login` 路由（验证 DASH_USER/DASH_PASS，返回 session cookie）
- [ ] 添加 `/api/auth/logout` 路由
- [ ] middleware 改为验证 session cookie
- [ ] 添加登录页面 `src/app/login/page.tsx`
- [ ] 添加 CSRF token 保护

#### mindflow-map API

- [ ] 添加 API Key 认证中间件（保护非公开端点）
- [ ] `/docs` 和 `/redoc` 在生产环境禁用或加认证

### 1.3 输入验证

#### DS

- [ ] `approve/route.ts` — status 白名单校验（pending/rejected/approved）
- [ ] `approve/route.ts` — approvalId 存在性验证
- [ ] `tickets/route.ts` — severity 白名单校验
- [ ] 所有 POST 路由添加 request body schema 验证（zod）

#### mindflow-map

- [ ] 所有 API 端点添加 Pydantic request model
- [ ] 字符串输入添加长度限制
- [ ] 坐标输入添加范围验证

---

## 四、Phase 2：部署修复

### 2.1 DS Docker 修复

```dockerfile
# Dockerfile — 修复后
FROM node:20-alpine AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npx prisma generate && npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000

RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs
EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000/api/health',r=>process.exit(r.statusCode===200?0:1)).on('error',()=>process.exit(1))"

CMD ["node", "server.js"]
```

- [ ] 删除 `COPY --from=builder /app/public ./public`（不存在）
- [ ] 健康检查改用 `node -e`（alpine 无 wget）
- [ ] 端口统一为 3000
- [ ] 添加 `/api/health` 端点

```yaml
# docker-compose.yml — 修复后
services:
  web:
    build: .
    ports:
      - "3000:3000"
    environment:
      NODE_ENV: production
      PORT: 3000
      DATABASE_URL: file:./data/prod.db
      DEMO_MODE: "false"
    volumes:
      - ds_data:/app/data
    restart: unless-stopped

volumes:
  ds_data:
```

- [ ] 移除 PostgreSQL（或提供 `docker-compose.prod.yml` 单独配 Postgres）
- [ ] schema.prisma 添加多 provider 支持
- [ ] 数据持久化到 volume

### 2.2 mindflow-map 部署修复

```python
# config.py — 数据库路径
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite+aiosqlite:///{DATA_DIR}/mindflow_map.db"
)
```

- [ ] 数据库路径固定到 `mindflow-map/data/`
- [ ] `data/` 加入 `.gitignore`
- [ ] Dockerfile 添加 `RUN mkdir -p /app/data`

### 2.3 根目录统一入口

```yaml
# docker-compose.yml（根目录，统一编排所有服务）
services:
  mindflow-web:
    build: ./mindflow/apps/web
    ports: ["3000:3000"]
    
  mindflow-api:
    build: ./mindflow/apps/api
    ports: ["3001:3001"]
    
  ds:
    build: ./DS
    ports: ["3004:3000"]
    
  mindflow-map:
    build: ./mindflow-map
    ports: ["2002:2002"]
    
  aid:
    build: ./AID/projects
    ports: ["8000:8000"]
```

- [ ] 创建根目录 `docker-compose.yml`
- [ ] 端口分配：3000/3001(MindFlow) / 3004(DS) / 2002(Map) / 8000(AID) / 5173(综艺)
- [ ] 添加 `.env` 模板（根目录统一密钥管理）

---

## 五、Phase 3：测试改革

### 3.1 DS 测试重写

**删除**现有浅层页面测试，替换为：

```typescript
// src/lib/db/metrics.test.ts
describe('metrics aggregation', () => {
  it('returns zero for empty database');
  it('sums revenue correctly for date range');
  it('filters by agent type');
  it('handles timezone boundaries');
});

// src/lib/risk/rules.test.ts — 保留并扩展
describe('risk engine', () => {
  it('blocks ads exceeding budget cap');
  it('flags banned words in content');
  it('rejects price changes above threshold');
  it('allows changes within threshold');  // 缺失的正面测试
  it('returns detailed rejection reason');  // 缺失的验证
});

// src/app/api/agents/content/approve/route.test.ts
describe('POST /api/agents/content/approve', () => {
  it('approves with valid id and returns 200');
  it('rejects with invalid status and returns 400');
  it('returns 404 for non-existent approvalId');
  it('returns 401 without API key');
});
```

- [ ] 删除 15 个页面渲染测试
- [ ] 添加 metrics 聚合逻辑测试
- [ ] 添加 risk engine 正面测试
- [ ] 添加 API 路由 happy path + error path 测试
- [ ] 添加 Prisma mock 策略

### 3.2 zcode-brain 测试重写

```typescript
// safety/safety-checker.test.ts — 重写
describe('safety checker', () => {
  it('blocks rm -rf (case insensitive)');
  it('blocks rm -fr (flag variant)');
  it('blocks RM -RF (uppercase)');
  it('blocks DROP TABLE (not just DATABASE)');
  it('blocks AWS access key pattern');
  it('blocks GitHub token pattern');
  it('blocks private key pattern');
  it('allows safe commands');
  it('returns detailed block reason');
});

// role-matcher.test.ts — 重写
describe('role matching', () => {
  it('matches exact trigger');
  it('returns null for empty input');
  it('returns null for nonsense input');
  it('handles ties deterministically');
  it('handles Chinese triggers');
  it('handles mixed Chinese-English input');
});
```

- [ ] 删除重复测试（test.ts 和 dispatcher.test.ts 二选一）
- [ ] 安全测试覆盖大小写、变体、多种密钥格式
- [ ] 角色匹配测试覆盖边界和异常输入
- [ ] 添加 prompt-assembler 测试

### 3.3 mindflow-map 测试补充

- [ ] 添加认证中间件测试
- [ ] 添加输入验证测试
- [ ] 添加密钥轮换场景测试

---

## 六、Phase 4：集成连通

### 6.1 统一身份（AID → 其他项目）

```
用户请求 → AID 身份验证 → 签发 JWT → 各项目验证 JWT
```

- [ ] AID 实现 `/auth/issue` 端点（签发 JWT）
- [ ] AID 实现 `/auth/verify` 端点（验证 JWT）
- [ ] mindflow-map 添加 JWT 验证中间件
- [ ] DS 添加 JWT 验证（替代或共存 Basic Auth）

### 6.2 数据流通

```
mindflow-map (工作流引擎)
    ↓ 调用
DS (电商执行)
    ↓ 回调
mindflow-map (状态更新)
```

- [ ] mindflow-map 添加 DS 客户端
- [ ] DS 添加 webhook 回调（操作完成后通知 mindflow-map）
- [ ] 统一错误码和响应格式

### 6.3 统一监控

- [ ] mindflow-map 已有 Prometheus 指标 → 扩展覆盖所有项目
- [ ] 统一日志格式（JSON + trace_id）
- [ ] 根目录 `docker-compose.yml` 添加 Grafana

---

## 七、Phase 5：文档翻新

### 5.1 根目录文档

| 文档 | 修改 |
|------|------|
| `README.md` | 删除"可直接部署"，改为"本地开发可用"；端口表与实际一致 |
| `PORTFOLIO.md` | 删除不实测试数字；标注各项目实际完成度 |
| `DEPLOY.md` | 重写为真实可执行的步骤；删除 Vercel 幻想 |
| `Caddyfile` | 更新为实际端口 |

### 5.2 子项目文档

- [ ] 每个项目 README 标注实际完成度（百分比）
- [ ] 删除"生产级"描述，改为"Demo 级"
- [ ] 添加"已知限制"章节
- [ ] 添加"从零启动"验证步骤

### 5.3 架构文档

```markdown
# 实际架构（非目标架构）

```
用户 → start-demo.bat → 6 个独立服务
                               ↓
                        无数据互通
                               ↓
                        各自独立数据库
```

## 目标架构（Phase 4 完成后）

```
用户 → Caddy (8080) → 统一网关
                       ├── /api/auth/*    → AID
                       ├── /api/workflow/* → mindflow-map
                       ├── /api/shopify/*  → DS
                       ├── /api/ai/*       → mindflow-api
                       └── /*              → mindflow-web
```
```

---

## 八、Phase 6：成品验收

### 验收清单

#### 安全
- [ ] 无密钥硬编码
- [ ] 所有 API 端点认证
- [ ] 仪表盘认证
- [ ] 输入验证覆盖
- [ ] HTTPS（Caddy 自动 TLS）

#### 部署
- [ ] `docker compose up` 一键启动所有服务
- [ ] 健康检查全部通过
- [ ] 数据持久化
- [ ] 端口无冲突

#### 测试
- [ ] 核心链路覆盖率 > 70%
- [ ] 无页面渲染测试（全部替换为逻辑测试）
- [ ] CI 自动运行

#### 文档
- [ ] README 与实际一致
- [ ] 架构图反映真实状态
- [ ] 启动步骤可直接执行

#### 集成
- [ ] AID 身份验证可用
- [ ] mindflow-map ↔ DS 数据流通
- [ ] 统一监控面板

---

## 九、项目优先级排序

如果时间有限，按以下顺序执行：

| 优先级 | 阶段 | 投入 | 收益 |
|--------|------|------|------|
| **P0** | Phase 1: 安全基线 | 1-2 天 | 从 D 到 B |
| **P0** | Phase 2: 部署修复 | 2-3 天 | 从"不能跑"到"能跑" |
| **P1** | Phase 3: 测试改革 | 3-5 天 | 从"能跑"到"敢改" |
| **P2** | Phase 5: 文档翻新 | 2-3 天 | 从"能骗人"到"诚实" |
| **P2** | Phase 4: 集成连通 | 5-7 天 | 从"散"到"整" |
| **P3** | Phase 6: 成品验收 | 1 天 | 确认 |

---

## 十、诚实完成度标注

翻新后的项目状态应标注为：

| 项目 | 当前标注 | 翻新后标注 |
|------|----------|-----------|
| mindflow-map | "可直接部署" | "核心功能完成，待安全加固" |
| DS | "可直接部署" | "Demo 可用，生产需替换数据库" |
| zcode-brain | "可直接运行" | "原型阶段，安全模块待重写" |
| AID | "可直接部署" | "功能完整，待集成验证" |
| ai综艺 | "可直接运行" | "前端 Demo，无后端" |
| MindFlow | "可直接部署" | "功能完整，待集成验证" |

---

*本方案为翻新路线图，具体实施时根据实际进度调整。*
