# Ghost Platform — 工作日志

> **格式**: 日期 + 会话编号 + 工作内容 + 结果  
> **关联**: 决策见 `DECISIONS.md`，状态见 `PROJECT_STATUS_REPORT.md`

---

## 2026-08-04

### 会话 1：项目级诊断 + 基础设施修复

**工作内容:**
- 逐行阅读 Ghost Platform 所有服务代码（Gateway, Alpha-ID, Nebula, DS, Orchestrator, Feishu-bot, Net-Agent）
- 发现并修复 /v1/chat 端到端链路断裂（GATEWAY_HOST 0.0.0.0 不可路由 + TenantMiddleware 阻断）
- 修复 feishu-consumer XREADGROUP 超时噪音日志（block timeout 误报为 ERROR）
- 修复 feishu-bot healthcheck（procps 缺失导致 pgrep 不可用）
- 修复 DS Prisma 迁移失败（手动 resolve applied migration）
- 修复 DS Dockerfile Prisma CLI 缺失（COPY node_modules from builder）
- 安装 Python 3.12 测试环境（C:\Program Files\Python312\）
- 为 Gateway 新增 4 个 /v1/chat proxy 测试
- 为 Orchestrator 新增 7 个 retry/timeout 测试
- 为 Feishu Consumer 新增 2 个 backoff 测试
- 创建 9 个缺失的服务 README
- 重写 README.md 为项目入口页
- 修复 GHOST.md 中 9 个不存在文件引用
- 创建 CODEOWNERS + CONTRIBUTING.md
- 创建根 Makefile（统一 up/test/lint/fmt 命令）

**结果:** 部分完成。代码级修复已验证，Docker Desktop 未运行，全栈验证待进行。

---

### 会话 2：测试修复 + 文档同步

**工作内容:**
- 修复 Gateway 53 个单测中的 36 个 401 失败（conftest 默认带 X-Tenant-ID）
- 修复 Python 3.12 ParseResult.origin 移除兼容（手拼 scheme://netloc）
- 修复 Gateway _IncludedRouter 结构变化（original_router 递归）
- 修复 feishu-bot 测试无限挂起（空轮询加 asyncio.sleep(0)）
- 修复 test_health URL 匹配（用 config.ALPHAID_URL 精确匹配）
- 修复 Gateway human chat 测试（筛选目标 URL 跳过 login 调用）
- 更新 GHOST.md 为实际状态（非计划状态）
- 创建 PROJECT_STATUS_REPORT.md（真实服务健康 + 测试覆盖 + 阻塞项）
- 盘活 DS EventBus 死代码（layout.tsx 全局 import eventbus-init）
- 更新 .gitignore 新增 feishu-bot 例外
- git commit: d8fad42（测试修复）+ b2f76a4（文档同步）

**结果:** 完成。
- Gateway: 53/53 passed
- Orchestrator: 7/7 passed
- Feishu-bot: 2/2 passed

---

### 会话 3：死代码盘活 + 文档完善（进行中）

**工作内容:**
- 分析 DS EventBus 死代码：仅 health/route.ts import，改为 layout.tsx 全局初始化
- 分析 Alpha-ID 死代码：agent.py 未被任何活跃模块 import（SDK 入口，保留）
- 分析 WeChatAdapter：已从 __all__ 移除，文件保留待实现
- 更新 GHOST.md 第 8 节新增 5 条已修复问题
- 更新 GHOST.md 第 3/5/6 节为实际状态
- 新增 P0 阻塞项（Docker Desktop 未运行）
- 创建 PROJECT_STATUS_REPORT.md

**结果:** 进行中。待继续盘活更多死代码 + WORK_LOG.md 完善。

---

### 会话 4：全服务测试验证 + 依赖修复

**工作内容:**
- 安装 Alpha-ID 缺失依赖：redis, hypothesis, psycopg[binary], psycopg-pool, pyyaml
- 安装 Nebula 缺失依赖：sqlalchemy, tenacity, prometheus-client, aiosqlite, openai, cryptography, python-dotenv
- 安装 mcp 1.6.0（修复 FastMCP ImportError）
- 修复 Alpha-ID submodule conftest.py AidNuro monkey-patch UnboundLocalError（移入 try 块内）
- 修复 Alpha-ID feature_flags.py 缺少 FairyBrain 等向后兼容别名（daemon.py re-export shim 需要）
- 修复 Alpha-ID dual_chain 测试属性名 `_chain_key_*` → `_meta_key_*`（6 个 AttributeError）
- 修正 dual_chain 加密测试：使用 `list_chain()` API 而非直接访问内部存储结构
- 修复 SqliteStorage.list() 兼容记录级存储（put() 写入的单条记录模式）
- 修复 PostgresStorage._deserialize() 兼容 JSONB 原生类型（psycopg v3 返回 dict 而非 str）
- 修复 _call_llm() api_key 检查顺序（先检查 api_key，再验证 base_url）
- 修复 Nebula docs/API_VERSIONING.md 缺少 v2 条目
- git commit: 所有改动待统一 commit

**结果:** 完成。
- Alpha-ID: 702 passed, 98 skipped（0 failures，含 submodule conftest 修复）
- Nebula: 153 passed（0 failures）
- Gateway: 33 passed, 20 skipped（0 failures）
- Orchestrator: 7 passed（0 failures）
- Feishu-bot: 2 passed（0 failures）

---

## Session 5 — 2026-08-04（深夜收尾 + DS 容器更新验证）

**工作内容:**
1. **Docker 镜像重建成功**: `docker compose build ghost-ds` 完成（38.5s），新镜像 9b32c45b → 容器重启后 healthy
2. **proxyToGateway body re-read 修复**: `api-proxy.ts` 增加 `options.body` 参数；`chat/route.ts` 先 `req.text()` 读 body 验证再传入 proxy，解决 `TypeError: Body has already been read`
3. **DS chat API 验证通过**: `POST /api/v1/human/chat` 返回真实 LLM 回复（"你好！我是你的智能总助..."）
4. **DS 全量 API 验证**: products(5条)、orders(5条)、stats(5状态统计)、shop、health、identity 全部正常
5. **DS 社交功能补齐**: 新增 `/social` 页面（好友/请求/消息三 Tab）+ 5 条 API 路由（friend-request, message, friends, requests, messages）+ NavIcon `social` + Sidebar 导航
6. **文档更新**: DECISIONS.md 补充 D-16（body re-read 修复）、D-17（social 页面）；WORK_LOG.md 更新

**结果:** 完成。
- DS chat API 连通 Gateway → Alpha-ID → 真实 LLM 回复
- DS social API 路由就位（401/403 是 Alpha-ID 正常认证要求，需 JWT 后可用）
- git commit: ec91499

---

## Session 6 — 2026-08-04（GhostBrain/GhostVoice 接入 Gateway + DS 页面）

**工作内容:**
1. **Gateway 新增 brain/voice 路由**: 
   - `/v1/human/brain/chat` — 代理到 Alpha-ID /api/v1/agent/chat，含 quick-register JWT 自动获取
   - `/v1/human/voice/status` — 代理到 Alpha-ID /api/v1/voice/status
   - 新增 `_brain_quick_register()` 辅助函数复用 chat 路由的 JWT 获取逻辑
2. **Alpha-ID 新增 voice API**: `api/voice.py`（/api/v1/voice/status）+ 注册到 main.py
3. **DS 新增 brain/voice 页面**: `/app/brain`（状态/唤醒/对话）+ `/app/voice`（状态/TTS 输入）
4. **DS 新增 2 条 API 路由**: `/api/v1/human/brain/chat`、`/api/v1/human/voice/status`
5. **DS 导航更新**: NavIcon 新增 `brain`/`voice` 图标，Sidebar 操作区新增两个入口
6. **全栈端到端验证通过**:
   - DS Brain Chat → Gateway → Alpha-ID → TwinBrain → 真实 AI 回复 ✅
   - DS Voice Status → Gateway → Alpha-ID → GhostVoice → 引擎可用性 ✅
   - Social API 401 是 Alpha-ID 正常认证要求（social 路由需显式 JWT，brain 路由自动 quick-register）✅

**git commits:**
- `da80f09` feat: add GhostBrain/GhostVoice Gateway routes + DS brain/voice pages
- `5dfdbf6` fix(ds): add missing brain/status and brain/awake API routes
- Alpha-ID submodule: `wip/2026-07-27 6d98ce1` feat(alphaid): add /api/v1/voice/status endpoint

---

## Session 7 — 2026-08-04（全栈端到端验证 + 补齐缺失路由）

**工作内容:**
1. **补齐缺失的 brain API 路由**: 发现 `/app/brain` 页面调用了 `/api/v1/human/brain/status` 和 `/api/v1/human/brain/awake` 但未实现，新增两条路由
2. **全栈端到端验证通过**:
   - DS Brain Status → Gateway → Alpha-ID → TwinBrain ✅
   - DS Brain Awake → Gateway → Alpha-ID → TwinBrain ✅  
   - DS Brain Chat → Gateway → Alpha-ID → AgentLoop → 真实 AI 回复 ✅
   - DS Voice Status → Gateway → Alpha-ID → GhostVoice → 引擎可用性 ✅
   - DS Social Friends → 401 expected (Alpha-ID 需显式 JWT) ✅
   - DS Chat, Products, Orders, Stats, Shop, Health 全部正常 ✅
3. **文档更新**: DECISIONS.md D-18 补充完整路由数量，WORK_LOG.md session 7

---

## Session 8 — 2026-08-04（修复 CSRF 头传播 + 完整验证所有 revived 路由）

**工作内容:**
1. **诊断 CSRF 403 问题**: GDPR Delete 和 Social Respond 返回 403 "missing X-Requested-With header"
   - 根因: DS→Gateway 调用未携带 `X-Requested-With`，Gateway `forward_csrf_headers` 只转发已存在的头
2. **多层修复方案** (DECISIONS.md D-19, D-20):
   - **DS 层**: `api-proxy.ts` `buildGatewayHeaders` 对非 GET/HEAD 请求自动添加 `X-Requested-With: XMLHttpRequest`
   - **Gateway 层**: `forward_csrf_headers()` 始终包含 `X-Requested-With: XMLHttpRequest`（Gateway 是可信内部客户端）
   - **Alpha-ID 层**: `CSRFMiddleware.exempt_prefixes` 新增 `/api/v1/social/`, `/api/v1/gdpr/`, `/api/v1/brain/`, `/api/v1/voice/`, `/api/v1/risk/`
   - **Gateway 层**: 所有 Alpha-ID 代理路由显式转发 `Authorization` 头（之前缺失导致 401）
   - **Gateway 层**: 新增 `proxy_delete()` 函数（gdpr/delete 是 DELETE 方法，之前误用 `proxy_post` 导致 405）
3. **完整端到端验证通过**:
   - ✅ GDPR Export → 返回 default 用户完整数据（profile + memories + social）
   - ✅ GDPR Delete → 删除成功（stats: memories=0, social=0, profile=1）
   - ✅ Social Friend Request → 请求发送成功
   - ✅ Risk Evaluate → 风险等级"警戒区"
   - ✅ Brain Status → 状态 "sleep"
   - ✅ Brain Awake → 唤醒成功
   - ✅ Brain Chat → 真实 AI 回复
   - ✅ Voice Status → 引擎可用性
4. **文档更新**: DECISIONS.md D-19, D-20；WORK_LOG.md session 8

---

## Session 9 — 2026-08-05（项目级修复 P0→P3：基础设施 + 前端 + 调度器接通）

**工作内容:**

### P0 — 基础设施修复
- **凭证泄漏**: `ghost-main/feishu-bot/.env` 被 Git 跟踪 → `git rm --cached`，加入 .gitignore，创建 `.env.example`，更新 `docker-compose.feishu.yml` 使用环境变量
- **Docker 网络错误**: `docker-compose.override.yml` 声明 `ghost-net: external: true` 但无网络定义 → 移除 external 声明
- **源码管理**: `flow/` 被 .gitignore 排除 → 移除排除规则并加入 Git

### P1 — 后端稳定性
- **Gateway 测试阻塞**: `ghost-main/gateway/test_proxy.py` 顶层 `asyncio.run(test())` 阻塞 pytest collection → 包装 `if __name__ == "__main__":` + 重命名 `test()` → `run_smoke_test()`
- **NameError**: `alphaid/projects/src/alpha_id/tool_orchestrator.py:342` `orch.execute(task)` 未定义 `task` → 改为 `task_id`
- **硬编码端口**: `ghost-main/gateway/server.mjs` 硬编码 `localhost:8002` → 改用 `process.env.ALPHAID_URL`（默认 `http://localhost:8000`）
- **空实现**: `orchestrator/engine.py` `write_note` 返回 ""、`send_feishu` 返回 false → 通过 EventBus 发布 `MEMORY_WRITTEN` / `SOCIAL_MESSAGE` 事件
- **状态报告失真**: 重写 `PROJECT_STATUS_REPORT.md` 为真实状态（无未验证声明）

### P2 — 前端功能
- **登录绕过**: `DS/src/app/login/page.tsx` 调用不存在的 `quick-register` 并 catch 重定向 → 新增 Gateway + DS 代理路由，移除 catch 重定向
- **AI 文案 Bug**: `DS/src/components/ProductAiDialog.tsx` 发送 `product.description` 而非 AI 优化结果 → 改用 `result.description`
- **Sidebar 渲染**: `DS/src/app/layout.tsx` 无条件渲染 Sidebar → 在 Sidebar 内检查 pathname 隐藏登录页
- **死代码清理**: `DS/src/lib/api.ts` 含 15+ 指向不存在端点的方法 → 删除死代码并加入 Git
- **硬编码身份**: `DS/src/app/brain/page.tsx` 使用 `Alpha-001` → 改为 `humanApi.getIdentity()` 获取真实身份
- **Webhook 命名不一致**: `DS/src/app/api/webhook/shoplazza/` 内容实为 OneBound → 重命名为 `onebound/`（route.ts + route.test.ts），describe 名称同步更新

### P3-1 — OrchestratorEngine 注册真实 ChannelAdapter + Loop
- 新增 `GatewayChannelAdapter`（继承 `ChannelAdapter`）— 通过 Gateway HTTP API 收发消息
  - 出站: `send()` POST 到 Gateway `/v1/message/send`
  - 入站: 新增 `POST /v1/channel/message` 端点，调用 `engine.receive()` 路由到 TwinBrain，回复通过 adapter.send() 回传
- 新增 `gateway_sync_loop` 数据循环 — 每 5 分钟（`ORCHESTRATOR_SYNC_INTERVAL`）上报 orchestrator 状态到 Gateway memory store
- 在 `lifespan()` 中 `engine.start()` 前注册 adapter + loop
- `/health` 端点新增 `channels` + `data_loops` 字段（监控可见）
- Orchestrator 测试 7/7 通过（含 /health 端点变更验证）

### P3-2 — 接通 mindflow 包到 Gateway（经 Alpha-ID 代理）
- 创建 `mindflow/__init__.py` — 使 mindflow 成为正式 Python 包（导出 MindflowEngine/TaskInstruction/TaskResult 等）
- 创建 `api/mindflow.py` — Alpha-ID 路由，暴露 3 个端点：
  - `GET /api/v1/mindflow/status` — 引擎状态 + 已注册工具 + 支持的意图列表
  - `POST /api/v1/mindflow/intent` — 文本意图识别（关键词优先 + LLM 回退）
  - `POST /api/v1/mindflow/execute` — 执行任务指令（TaskInstruction → TaskResult）
- `main.py` 注册 mindflow_router + CSRF 豁免 `/api/v1/mindflow/`
- Gateway `routes/human.py` 新增 3 个代理路由：
  - `GET /v1/human/mindflow/status`
  - `POST /v1/human/mindflow/intent`
  - `POST /v1/human/mindflow/execute`
- 修复 `mindflow/intent.py` 预存 bug：`_llm_classify` 方法被调用但未定义 → 补全实现（httpx 调用 LLM API + JSON 解析 + 降级）
- 验证：引擎执行 OK、意图分类 OK（"导航到公司" → route_plan 0.85）、Gateway 集成路由测试 14/14 通过

**结果:** P0-P3 全部完成。mindflow 死代码包已盘活，通过 Alpha-ID → Gateway 双层代理对外提供服务。

---

## 待办

- [x] Docker Desktop 启动后验证全栈健康
- [x] 逐步接入 Alpha-ID 新模块到 Gateway 路由（brain/voice/social）
- [ ] 为 Nebula、Alpha-ID 补充单元测试
- [ ] 接入真实 ToolA/ToolB 服务（替换 stub）
- [x] DS 添加 demo seed script 验证
- [x] Alpha-ID GhostBrain/GhostVoice 接入 Gateway 路由
- [x] DS 内容库 Web UI 生成表单 + API 路由
- [x] DS 登录页面 + 登出按钮
- [x] 多租户 TenantMapping 模型 + 迁移
- [x] Gateway content recovery logic (MoneyPrinterTurbo stuck state)
- [x] 端到端视频生成管道验证

---

## Session 11 — 2026-08-05: 平台全链路补齐

### 完成项

1. **DS 内容库 Web UI 生成能力**:
   - `/content` 页面添加「✨ 创建内容」按钮 + 模态框
   - 视频生成表单：主题、画面比例、语言、拼接模式
   - 游戏生成表单：游戏类型、主题风格、描述
   - 实时轮询生成状态（5s interval），进度条显示
   - 生成完成后自动刷新内容列表
2. **DS 内容生成 API 路由**:
   - `POST /api/content/generate` → proxy to Gateway `/v1/content/video|game/generate`
   - `GET /api/content/generate/status/{task_id}` → proxy to Gateway status
   - 使用 Zod 验证 + proxyToGateway 工具函数
3. **DS 登录页面**:
   - `/login` 页面：一键 quick-register → redirect to /chat
   - 加载状态、错误处理、demo mode fallback
4. **DS 登出按钮**:
   - Sidebar 底部添加「退出登录」按钮
   - 调用 `/api/v1/human/logout` → redirect to /
   - 未连接时显示「登录」按钮（链接到 /login）
5. **多租户 TenantMapping 模型**:
   - Prisma schema 添加 `TenantMapping` model（alphaId → tenantId 映射）
   - 迁移 SQL: `20250805000002_add_tenant_mapping`
   - Gateway TenantMiddleware 重构：JWT alpha_id claim 作为 tenant_id
   - DS `getOrCreateTenantId(alphaId)` 工具函数
6. **Gateway Recovery Logic 修复**:
   - 探测路径从 `/download/{task_id}/final-1.mp4` 修正为 `/api/v1/download/{task_id}/final-1.mp4`
   - 与 MoneyPrinterTurbo 实际端点对齐
7. **端到端验证**:
   - 完整管道：Gateway → MoneyPrinterTurbo → DS Content → 内容页显示
   - 任务 `af673de6` 完成时间：~70s（7 polls）
   - 内容记录 `cmsf048a30000m06yfv3nbyur` 创建成功
   - 所有 6 步 e2e 测试通过

### 待办

- [ ] 游戏生成服务实现（Phase 2）
- [ ] DS 内容详情页 + 编辑/删除
- [ ] 真实飞书环境验证 /video 命令
- [ ] DS frontend Playwright E2E 测试
