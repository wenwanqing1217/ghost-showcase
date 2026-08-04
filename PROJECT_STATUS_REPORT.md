# Ghost Platform — 项目状态报告

> **生成时间**: 2026-08-04 | **验证方式**: 逐行代码阅读 + 单元测试

## 1. 服务健康状态

| 服务 | 端口 | 状态 | 验证方式 | 备注 |
|:-----|-----:|:-----|:---------|:-----|
| Gateway | 18080 | ✅ 代码就绪 | 53 单元测试通过 | TenantMiddleware + 路由 + 代理已修复 |
| Alpha-ID | 8000 | ⚠️ 待验证 | 部分测试可用 | 35% 有效代码率，新模块未全部接入 |
| Nebula | 2002 | ⚠️ 待验证 | 代码已读 | 10+ route groups，需 Docker 运行 |
| Ghost DS | 3001 | ⚠️ 待验证 | 代码已读 | Next.js 14 + Prisma，需 Docker 运行 |
| Orchestrator | 19090 | ✅ 代码就绪 | 7 单元测试通过 | ToolA/ToolB retry + timeout 已实现 |
| Feishu Bot | — | ⚠️ 待验证 | 代码已读 | echo 模式可用，需 Docker 运行 |
| Feishu Consumer | — | ✅ 代码就绪 | 2 单元测试通过 | XREADGROUP 超时噪音已修复 |
| Net-Agent | 18180 | ⚠️ 待验证 | 代码已读 | 需 Docker 运行 |
| Flow | 3036 | ⚠️ 待验证 | 代码已读 | 需 Docker 运行 |
| Redis | 6379 | ⚠️ 待验证 | — | Docker 未运行 |
| PostgreSQL | 5432 | ⚠️ 待验证 | — | Docker 未运行 |

## 2. 测试覆盖状态

| 项目 | 测试数 | 通过 | 失败 | 备注 |
|:-----|:------:|:----:|:----:|:-----|
| Gateway | 53 | 53 | 0 | 全绿 ✅ |
| Orchestrator | 7 | 7 | 0 | 全绿 ✅ |
| Feishu-bot | 2 | 2 | 0 | 全绿 ✅（之前无限挂起已修复） |
| Nebula | — | — | — | 需独立运行 |
| Alpha-ID | — | — | — | 需独立运行 |
| Ghost DS | — | — | — | 需 Docker 运行 |
| E2E | — | — | — | 需 Docker Compose 全栈 |

## 3. 最近修复（2026-08-04）

1. **Gateway 单测 401 修复** — conftest 默认带 X-Tenant-ID，53/53 passed
2. **Python 3.12 兼容** — `urlparse(...).origin` → 手拼 scheme://netloc
3. **_IncludedRouter 兼容** — `_all_route_paths()` 支持 `original_router`
4. **feishu-bot 测试挂起** — 空轮询加 `await asyncio.sleep(0)`，2/2 passed
5. **test_health URL 匹配** — 用 `config.ALPHAID_URL` 精确匹配
6. **doubao/human chat 测试** — 筛选目标 URL（跳过 login/register 调用）

## 4. 阻塞项

- **Docker Desktop 未运行** — 无法验证全栈健康状态
- **Docker Desktop 未运行** — 无法运行 E2E 测试
- **Alpha-ID 新模块未接入** — OrchestratorEngine, MCP Tools, Smart Capture 等已实现但路由未全部激活

## 5. 下一步行动

1. 启动 Docker Desktop → `make up` → 验证全栈健康
2. 逐步接入 Alpha-ID 新模块到 Gateway 路由
3. 为 Nebula、Alpha-ID 补充单元测试
4. 接入真实 ToolA/ToolB 服务（替换 stub）
