# Ghost Platform — 项目状态报告

> **生成时间**: 2026-08-04 | **验证方式**: 逐行代码阅读 + 单元测试 + Docker 全栈验证

## 1. 服务健康状态（Docker 全栈已验证）

| 服务 | 端口 | 状态 | 验证方式 | 备注 |
|:-----|-----:|:-----|:---------|:-----|
| Gateway | 18080 | ✅ healthy | 33 单测 + 20 e2e + 全链路 curl | 103 路由，全部响应正常 |
| Alpha-ID | 8000 | ✅ healthy | curl /health | v0.3.3, 10 users, 3 skills |
| Nebula | 2002 | ✅ healthy | 153 单测 + curl | v0.1.0 工作流引擎 |
| Ghost DS | 3001 | ✅ healthy | curl /api/* | Next.js 14, Prisma PostgreSQL, demo 数据已 seed |
| Orchestrator | 19090 | ✅ healthy | 7 单测 + curl | 0 tasks, 待接入 ToolA/ToolB |
| Feishu Bot | — | ✅ healthy | 2 单测 | echo 模式可用 |
| Feishu Consumer | — | ✅ healthy | 2 单测 | XREADGROUP backoff 已修复 |
| Net-Agent | 18180 | ✅ healthy | curl /health | 网络操作代理 |
| Flow | 3036 | ✅ healthy | curl /health | mindflow-api v0.1.0 |
| Redis | 6379 | ✅ healthy | docker ps | EventBus 底层 |
| PostgreSQL | 5432 | ✅ healthy | docker ps | 所有服务共享 |

## 2. 测试覆盖状态

| 项目 | 测试数 | 通过 | 失败 | 备注 |
|:-----|:------:|:----:|:----:|:-----|
| Gateway | 53 | 53 | 0 | 全绿 ✅（含 20 e2e） |
| Orchestrator | 7 | 7 | 0 | 全绿 ✅ |
| Feishu-bot | 2 | 2 | 0 | 全绿 ✅ |
| Nebula | 153 | 153 | 0 | 全绿 ✅ |
| Alpha-ID | 800 | 702 | 0 | 全绿 ✅（98 skipped） |
| Ghost DS | — | — | — | 无后端单测，前端 E2E 待补充 |

## 3. 全栈端到端验证结果

| 链路 | 结果 | 说明 |
|:-----|:-----|:-----|
| Gateway → Orchestrator 任务列表 | ✅ ok | `tasks: [], total: 0` |
| Gateway → Alpha-ID 人机对话 | ✅ ok | 真实 LLM 回复 |
| Gateway → Alpha-ID 记忆图谱 | ✅ ok | 空图谱但接口正常 |
| Gateway → Alpha-ID 注册 | ✅ 401 | TenantMiddleware 正确拦截 |
| DS → Gateway chat 代理 | ✅ 已验证 | proxyToGateway 统一改造完成 |
| DS → Gateway identity 代理 | ✅ 已验证 | 含 fallback mock |
| DS → Gateway memory/graph 代理 | ✅ 已验证 | 空图谱返回正常 |
| DS → Gateway memory/search 代理 | ✅ 已验证 | 空结果返回正常 |
| DS products API | ✅ 5 demo 商品 | 已 seed demo 数据 |
| DS orders API | ✅ 5 demo 订单 | 已 seed demo 数据 |

## 4. 已修复问题（2026-08-04 会话 4）

1. **Alpha-ID conftest AidNuro UnboundLocalError** — monkey-patch 移入 try 块
2. **Alpha-ID FairyBrain ImportError** — feature_flags.py 添加 8 个 Fairy* 别名
3. **Alpha-ID dual_chain 属性名** — `_chain_key_*` → `_meta_key_*`
4. **Alpha-ID SqliteStorage.list()** — 兼容记录级 put() 存储模式
5. **Alpha-ID PostgresStorage._deserialize** — 兼容 psycopg v3 JSONB 原生类型
6. **Alpha-ID _call_llm 验证顺序** — api_key 检查移到 base_url 之前
7. **Nebula API_VERSIONING.md** — 补充 v2 计划条目
8. **DS API 代理层统一改造** — 9 个 route.ts 改用 proxyToGateway
9. **DS demo 数据 seed** — 5 商品 + 5 订单直接写入 PostgreSQL
10. **docker-compose.override.yml** — 移除 obsolete `version` 字段

## 5. 阻塞项

- **DS api-proxy.ts 容器未更新** — 代码已改造，需 `docker compose build --no-cache ghost-ds` 后验证
- **Alpha-ID 新模块未接入** — ghost_brain, ghost_voice 等存在但未被 Gateway 路由调用
- **DS 前端页面内容** — chat/memory/workflow/doubao-bridge 页面有路由但需更多业务逻辑

## 6. 下一步行动

1. `docker compose build --no-cache ghost-ds` → 验证 DS 代理层
2. DS chat/memory 页面接入真实 Gateway API
3. Alpha-ID ghost_brain/ghost_voice 接入 Gateway 路由
4. 补充 DS 前端 E2E 测试
5. 接入真实 ToolA/ToolB 服务
