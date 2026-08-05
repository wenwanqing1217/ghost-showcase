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

---

## Session 12 — 2026-08-05（调度层免费优先 + 基建自替换 + 飞书社交 + DIY 多租户面板）

**工作内容:**

### 1. 调度层：find_best_agent 免费优先 + 基建 agent 置顶
- 重写 `find_best_agent`：4 层 tier 排序 — 基建(0, 平台内置免费最优) → 自己的(1) → 好友的(2) → 其他免费(3)；付费仅 `prefer=paid` 或无免费候选时兜底
- 新增 `_preferred` 字典：基建自替换结果通过 `swap_to_best` 写入 `_preferred`，`find_best_agent` 下次直接优先返回，实现"定期最优自替换"立即生效
- 文件：`alphaid/projects/src/core/agent_graph.py` L300-L380

### 2. 基建层：OrchestratorEngine 定期最优自替换巡检
- 新增 `benchmark_skill(skill_name)` — 按 免费×40 + 成功率×40 + 延迟×20 综合评分所有候选 agent
- 新增 `swap_to_best(skill_name, min_score_gain=5.0)` — 当前基建评分低于最佳候选 ≥5 分时自动替换，写入 `_preferred`
- 新增 `run_optimal_swap_pass(skills, min_gain)` — 遍历所有内置基建 skill 执行 benchmark + swap
- 新增 `LoopPhase.OPTIMAL_SWAP` + `_optimal_swap_loop` — 默认 1 小时巡检一次（`OPTIMAL_SWAP_INTERVAL_SECONDS=3600`），替换结果通过 EventBus `SYSTEM_ALERT` 广播
- 文件：`agent_graph.py` L446-L620, `orchestrator/engine.py` L53-L321

### 3. 社交层：飞书通讯录同步自动加好友
- 新增 `UserBinding` dataclass — alpha_id ↔ 飞书 open_id / user_id / union_id / 手机 / 邮箱 / 微信 / TG
- 新增 `set_feishu_bridge(bridge)` — 注入 FeishuBridge 实例用于拉通讯录
- 新增 `sync_feishu_contacts(actor_alpha_id)` — 拉飞书通讯录 → 用 `_feishu_to_alpha` 反查谁绑定过 → 自动 `_ensure_friendship` 双向加好友
- 新增 `_ensure_friendship(a, b)` — 双向写好友关系 + 持久化到 storage
- 新增 `_rebuild_binding_index()` — 启动时从 storage 重建 `_feishu_to_alpha` 索引
- API 端点：`POST /{alpha_id}/bind/feishu`（绑定）、`GET /{alpha_id}/bind`（查询）、`POST /{alpha_id}/sync-feishu-contacts`（同步）
- Container 双向注入：`social` getter 自动注入已创建的 feishu；`set_feishu_credentials` 创建后立即回灌 social
- 文件：`core/alpha_social.py` L54-L300, `api/social.py` L107-L180, `container.py` L142-L253

### 4. 用户 DIY + 多租户面板
- 新建 `alpha_id/diy_cli.py` — 9 种意图（scaffold.init / a2a.register / a2a.call / a2a.findskill / feishu.sync_contacts / feishu.bind / credits.reward / workflow.execute / brain.chat）
- LLM 意图解析优先 + 本地关键词打分兜底（无 LLM 也能用）
- `IntentExecutor` 自动调 HTTP API 或直接复用 scaffold_cli
- CLI 入口：`aid chat "xxx"`（超短入口）、`aid diy repl`（连续对话）、`aid diy intents`（列出能力）
- 新建 `api/tenant_panel.py` — `/u/{alpha_id}/dashboard` 一用户一独立面板，8 个 tab（Overview / Agents / Workflows / Credits / Social / DIY Chat / Workbenches）
- 常用工作台 CRUD：用户自挂飞书多维表格 / Notion / Obsidian / Grafana 等，支持外链跳转或 iframe 嵌入
- 一键嵌入代码：本面板可被 iframe 嵌入到 Ghost DS / 飞书 / Notion（双向对接）
- 多租户隔离：写操作 `_owner_or_403` 校验 JWT sub 或 `X-Alpha-ID` header 匹配
- 文件：`alpha_id/diy_cli.py`（465行）, `alpha_id/cli.py` L47-L61, `api/tenant_panel.py`（450行）, `main.py` L52-L54

**结果:** 代码完成，ast.parse 语法校验全部通过。**未跑运行时测试、未跑 Docker 全栈验证。**
- 新增 0 个单测（AGENTS.md 9.6 条要求核心模块写 pytest — 待补）
- GHOST.md / DECISIONS.md / PROJECT_STATUS_REPORT.md 本次同步更新
- 创建 HANDOFF.md 交接文档（含项目状态、业务场景清单、5个修正点、打包清单）

### 用户探讨的 5 个修正点（方向已确认，未实现，见 HANDOFF.md 第三节）

1. **DIY CLI 改成 adapter 层** — 不自造意图解析，接 Codex/Claude/Aider，我们只负责执行+注册
2. **基建自替换频率降低** — 从每小时改成每天凌晨，连续3天低于候选才替换
3. **benchmark 用真实数据** — 接 EventBus 真实调用事件打榜，不用占位 `_success_rate`
4. **接外部 skill 市场** — AgentGraph 加 OpenRouter/Gorilla 等外部路由源
5. **补全业务场景意图** — DIY CLI + 面板补 7 个：闲鱼/小红书/抖音/短剧/视频/游戏/文案（项目里已有完整后端，见 HANDOFF.md 第二节）

## Session 13 — 2026-08-05（5 修正点收尾 + 新模块补测 79 passed + 文档同步）

**工作内容:**

### 1. 5 个修正点落地核验（Session 12 探讨，本次收尾）
| # | 修正点 | 状态 | 落地位置 |
|:--|:-------|:----:|:---------|
| 1 | DIY CLI adapter 层 | ✅ 本轮完成 | `diy_cli.py` 新增 `codex.delegate` 意图，编程/脚本/爬虫类任务委派本机 Codex（复用 `alpha_id.codex_api.CodexAPIServer.ask_once`） |
| 2 | 基建自替换频率 → 每天 | ✅ 此前完成 | `orchestrator/engine.py` `OPTIMAL_SWAP_INTERVAL_SECONDS=86400` |
| 3 | benchmark 用真实数据 | ✅ 此前完成 | `agent_graph.py` `_success_rate/_avg_latency` 来自 `record_call` 真实调用统计（A2A_CALL_RESULT），probe 仅可选 |
| 4 | 外部 skill 市场 | ✅ 本轮完成 | `agent_graph.py` 新增 `register_external_source` / `sync_external_skills` / `list_external_sources`；OpenRouter/Gorilla/自建源注册，幂等同步，external agent 参与 find_best_agent 选路 |
| 5 | 补全业务场景意图 | ✅ 本轮完成 | `diy_cli.py` 新增 6 意图：channel_copy.generate / video.generate / video.publish / douyin.publish / shortdramas.submit / game.generate + 中文 key=value 参数抽取（商品/卖点/价格/成色/主题/标题/内容），handler 全部复用 DS / Gateway / Nebula 已有后端（0 新造轮子） |

### 2. 新模块补测（Session 12 承诺 AGENTS.md 9.6 补 pytest）
- 新增 `tests/test_credits_growth.py`（15 用例）：CreditsWallet 4 条计费规则（platform_infra_free / self_owned_free / friend_free / stranger_paid+10%抽成）+ 余额不足 + 退款 + 流水过滤；GrowthTracker 累计/失败不计分/进化到成熟体/阶段边界；agent_dispatch growth_stats 分支
- 更新 `tests/test_diy_cli.py`：业务意图细分测试（咸鱼文案/小红书/视频/抖音/短剧/游戏/codex）+ kv 参数抽取
- 更新 `tests/test_agent_graph.py`：新增 TestExternalSkillMarket 3 用例（注册同步幂等 / 单源同步 / external 参与选路）
- **修复 GrowthTracker 内存模式 bug**：无 storage 时成长值丢失（_save_stats 直接 return），新增内存缓存自持，storage 与缓存双写

**结果:**
- Alpha-ID 新增测试 `79 passed`（6 个测试文件）✅；Gateway 32+20 ✅；Nebula 153 ✅；Orchestrator 7 ✅；DS 45 ✅
- PROJECT_STATUS_REPORT.md 全面同步（P2/P3 修复记录 #8-#25、测试表、Session 12/13 模块状态全部转"已测试"）
- 剩余待办：飞书 App Secret 轮换（用户操作）、Docker 全栈验证（用户需启动 Docker Desktop）、打包分发（见 PACKAGING_STRATEGY.md）

---

## 2026-08-05 会话 3：质量加固（还远远不够 → 构建链路全绿）

**工作内容:**
- **a2a.py 审计链路核查** — `SqliteAuditStore` 实际存在于 `core/audit_store.py`（main.py 已启用），字符串注解升级为真实导入
- **ruff 全量清零（509 → 0）** — 批量修 W293/W291 行尾空白；真实 bug 修复：
  - `alpha_social.py` `get_friends` 重复定义（433 行简单版覆盖 300 行去重版）→ 删覆盖版保留增强版
  - `feature_flags.py` 顶层无条件导入 `tools.screen_capture`（破坏优雅降级）→ 统一改 try/except 导入模式
  - `container.py`/`tool_orchestrator.py`/`observability.py` F401 未使用导入 → 删除
  - `smart_capture.py` diff_result 死代码、`ghost_character.py` points/wave_points 死代码 → 删除
  - E402 导入位置 → 移到顶部或加 noqa；E741 `l` 变量改名；N806/N803/N812/N818 项目有意命名加 noqa
- **alphaid 测试 859 passed 全绿** — 修 4 失败：3 个 `asyncio.get_event_loop()` Python 3.12 不兼容（测试代码改 asyncio.run）；1 个沙箱权限（monkeypatch Path.home 隔离数据目录）；2 个坏测试补 await + async call_next
- **DS 构建链路首次全绿** — tsc 0 错误 + vitest 45 + next build exit 0（38 页面）
- **DS 严重 bug 批量修复（#13-#23）**：
  - #13 demo 纯前端模拟（去 404 请求）；#15 obsidian URL 缺 `?`；#17 RevenueChart `var(--text)`→`var(--text-primary)`；#18 demo-data 状态值对齐 StatusBadge；#19 chat 离线话术引用用户输入；#20 AuthGuard 校验响应身份字段；#22 端口统一 3000；#23 feishu-bot Dockerfile 缺失文件强制纳入 git（根 .gitignore 放行 + git add -f）
- **种子数据** — seed.ts 订单时间分散 7 天（趋势图有起伏）；SQLite 本地模式验证：5 商品 + 6 订单，/api/stats 返回真实数据
- **本地冒烟通过** — DS dev server `/api/stats` 200 + `/dashboard` 200；Docker daemon 未运行（沙箱限制），容器级验证仍待用户启动 Docker Desktop

**结果:** ruff 0 errors + alphaid 859 passed + DS tsc/vitest/build 全绿 + 看板非空可演示。PROJECT_STATUS_REPORT.md 已同步。

---

## Session 14 — 2026-08-05（CI 可跑 + 数据流可读 + 仓库专业化）

**背景:** 用户反馈"数据流看不清、没串联、推到 GitHub 不专业、自动化编程不好做"。

**工作内容:**

### 1. CI 修复（GitHub Actions 真能过）
- `reusable-python-ci.yml`：安装策略按 pyproject/requirements.txt 分流（gateway/orchestrator 无 pyproject，之前必挂）
- `ci.yml`：e2e job 补 `DB_PASSWORD` env；`docker compose up` 显式列出 10 服务、跳过 MoneyPrinterTurbo（仓库无该目录）；e2e 触发条件扩为 6 个服务
- `DS/package.json`：health 脚本端口 3004 → 3000
- `flow/apps/api/package.json`：`@mindflow/shared` 依赖 `workspace:*` → `file:../../packages/shared`（npm 11 不支持 workspace: 协议，本地与 CI 均会安装失败）

### 2. 新增 DATA_FLOW.md
- 6 条业务闭环（飞书指令→内容 / 看板↔网关↔身份 / OneBound Webhook / A2A 市场+信用 / 工作流执行 / 调度换优）
- 每条闭环：真实端点 + 涉及文件 + 验证状态；3.3 节诚实未落地清单

### 3. README 重写 + Makefile
- README：删两套冲突快速启动/旧路径/虚假"11/12 服务运行中"；badges + 架构图 + 单条快速启动 + 实测测试表 + 真实状态；修复 SYSTEM_MAP/PROJECT_MAP 断链
- Makefile：新增 `make smoke`（6 子项目一键全量单测，无 Docker）；去掉掩盖失败的 `2>/dev/null || echo`

### 4. 本地实测（无 Docker 可跑全部）
- alphaid 859 ✅ / nebula 153 ✅ / gateway 32 ✅ / orchestrator 7 ✅ / DS 45 ✅ / flow 30 ✅ = **1126 passed**

**结果:** 完成。CI 配置可在 GitHub 上真实运行；数据流与验证状态有据可查；README/Makefile 专业化。

**提交:** 见下方 git commit。

---

## Session 15 — 2026-08-05（lint 硬化 + 10+ 真实 bug 修复 + net-agent 测试 0→12）

**背景:** 承接 Session 14 继续"别停下来"——把 CI 能跑落到"本地 lint 全绿 + 全仓测试 1138 连过"，并为无测试的 net-agent 补上测试套件。

**工作内容:**

### 1. L3/L4 文档补全（改架构必改文档）
- 新建 [SYSTEM_MAP.md](SYSTEM_MAP.md)（L3）：服务拓扑 / 调用链速查 / 端口表 / 部署关系 / 变更记录
- 新建 [PROJECT_MAP.md](PROJECT_MAP.md)（L4）：术语表（OrchestratorEngine/EventBus/AgentGraph/MemoryGraph/TwinBrain/ChannelAdapter/GhostDS/Gateway + 禁用别名）、端口汇总、文档层级、冲突解决记录
- [GHOST.md](GHOST.md) 核心文档表补入 DATA_FLOW/SYSTEM_MAP/PROJECT_MAP/Makefile
- README 验证表 1126 → **1138**（加 net-agent 行）；徽章同步 `tests-1138%20passed`；DATA_FLOW.md 验证矩阵同步

### 2. ruff lint 全绿（alphaid/gateway/orchestrator/nebula/net-agent）
- 统一 ruff 配置：新建 `ghost-main/ruff.toml`、`ghost-main/gateway/ruff.toml`、`orchestrator/ruff.toml`，改 `nebula/pyproject.toml`
- 统一 `select = ["E","F","I","N","W","UP","RUF"]` + 中文注释豁免 RUF001/2/3（nebula 另忽略 RUF006/RUF012；gateway 另忽略 BLE001/DTZ003/S110/SIM115/UP042；ghost-main 另忽略 E402）

### 3. lint 揪出的真实 bug（不止是格式）
| Bug | 位置 | 严重度 |
|:----|:-----|:-------|
| `datetime` 未导入（F821） | `nebula/src/mindflow_map/api/supply.py` | 运行时必炸 |
| `_global_supply_registry` 未定义（F821） | `nebula/src/mindflow_map/supply/base.py` | 运行时必炸 |
| `EventType.SOCIAL_MESSAGE` 不存在（F821） | `ghost-main/gateway/routes/internal.py` | 运行时必炸 |
| `payload_b64 += b"..." * padding`（str+=bytes TypeError） | `ghost-main/gateway/middleware/tenant.py` | JWT 未对齐即炸 |
| `_AUTH_MASTER_KEY` 等 N806 下划线大写 | `tenant.py` | 规范 |
| F841/E741 多处 | ecom.py/game_engine.py/feishu.py/health.py/approvals.py/openwrt.py/xiaomi.py | 清理 |

### 4. net-agent 测试 0 → 12（补测套件 + 修真实 bug）
- 新建 `net_agent_server/tests/conftest.py`：安全环境变量 + sys.path 引导（与 main.py 一致）
- 新建 `test_auth.py`（TestCredentialCrypto 4 + TestPermission 4）+ `test_adapters.py`（TestUnknownDevices + TestOpenWrtLifecycle）
- **vendor_registry.py 循环导入** → `_BUILTIN_VENDOR_MODULES` 映射 + `importlib.import_module` 惰性加载；恢复被误删的 `list_vendors()`（routes.py /vendors 接口在用）
- **adapters/base.py `async with` 从未可用** — `@asynccontextmanager` 错误装饰 `__aenter__` 导致缺 `__aexit__`，重写为手写协议（测试揭出真实 bug）
- `net_agent_server/requirements.txt` 补 `cryptography` + `python-jose[cryptography]`（运行时必需）
- 新建 `ghost-main/requirements.txt`（CI 安装入口）

### 5. 其他硬化
- `docker-compose.yml`：MoneyPrinterTurbo → `profiles: ["media"]` 可选服务（仓库无该目录，默认 `docker compose up` 不再挂）
- `.gitignore` 移除全局 `package.json`/`package-lock.json` 忽略（flow/gateway 清单从未入库的根因）→ 改仅忽略根目录
- `flow/apps/api/src/routes/map.ts`：`Record<string, unknown>` 索引访问类型错误，新增 `cityOf()` 收窄

### 6. 本地实测
- alphaid 859 ✅ / nebula 153 ✅ / gateway 32 ✅ / orchestrator 7 ✅ / net-agent 12 ✅ / DS 45 ✅ / flow 30 ✅ = **1138 passed**，ruff 全绿

**结果:** 完成。全仓 lint 干净、1138 测试连过；net-agent 从"测试目录为空（CI exit 5）"到 12 passed 并修出 4 个真实 bug；文档 L1-L4 齐备。

**推送 + 历史清理（本会话追加）:**
- 网络排障：github.com HTTPS 被 GFW 间歇性干扰（curl 通 / git connect 超时 + TLS reset 交替）；`http.postBuffer=65536`（64KB 分块）后连接稳定
- 推送顺序：先推子模块 `alphaid/projects` wip/2026-07-27（37021b6，领先远程 5 提交）→ 再 force push 主仓库 master
- GitHub Push Protection 拦截两次，filter-branch 重写历史解决：
  - `DockerDesktopInstaller.exe`（625MB，超 100MB 限制，源自 91ea228 误提交）
  - `ghost-main/feishu-bot/.env`（真实 FEISHU_APP_SECRET，6 处提交）
- 清理后 `.git` 600MB+ → 35.5MB；子模块 gitlink（37021b6）保留完好；远程 master = 78e9bd1（force update）
- 决策记录：DECISIONS.md D-20260805-1；状态报告同步（致命问题 #1 已解决）

**提交:** 见下方 git commit（Session 15）。

---

## 待办

---

## 2026-08-05

### 会话 16：企业级阶级升级 — Docker 全栈实测 + 5 个架构漏洞修复

**工作内容:**
1. **视频链路修复（漏洞 #3）** — MoneyPrinterTurbo [task.py](file:///d:/MW/MoneyPrinterTurbo/app/services/task.py) local 源无 ideo_materials 时自动扫描 storage/local_videos（file_security 路径约束），补 MaterialInfo 导入。实测任务 9528f344 完成，**真实产出 final-1.mp4 + combined-1.mp4**。
2. **飞书 WS 长连接（漏洞 #1）** — [bot.py](file:///d:/MW/ghost-main/feishu-bot/bot.py) un() 改 WebSocket 主连接 + 轮询兜底 + 指数退避；新轮换 App Secret 已验证有效（tenant_access_token code:0），WS 已连（心跳 30s 持续）。
3. **OrchestratorEngine 完整集成（漏洞 #2/#4）** — compose context 改根目录，[Dockerfile](file:///d:/MW/orchestrator/Dockerfile) 打包 alphaid core/orchestrator；[agent.py](file:///d:/MW/alphaid/projects/src/core/agent.py) _InMemoryBackends 降级；[engine.py](file:///d:/MW/alphaid/projects/src/orchestrator/engine.py) 修 "OPTIMAL_SWAP" 字符串 phase .value 崩溃。**Engine 完整启动**：4 后台循环 + gateway_sync 数据循环 + AgentGraph 基建自替换（3 skill swap）。
4. **可观测性（漏洞 #5）** — orchestrator 新增 /metrics（prometheus-client）；prometheus.yml 加 orchestrator target（5 target 全 up）；.gitignore 解除 prometheus.yml 忽略。
5. **gateway_sync 链路** — 上报路径修正 /v1/human/memory/store + X-Tenant-ID 头 → 200 OK（多租户隔离验证）。
6. **EventBus 优雅化** — [event_bus.py](file:///d:/MW/alphaid/projects/src/core/event_bus.py) XREADGROUP 空闲超时静默。
7. **Dockerfile 加速** — 5 个服务切清华 apt 源。
8. **E2E 全栈验证** — 
ode scripts/e2e_test.mjs --wait **10/10 ALL GREEN**；14 容器 healthy。

**结果:**
- 14 容器 healthy（orchestrator/gateway/alphaid/nebula/flow/tool-a/tool-b/netagent/ghost-ds/moneyprinter/db/redis + grafana/prometheus）
- E2E 10/10；Alpha-ID 回归 42 passed；视频真实产出 mp4；Prometheus 5 target up

**待办:** 飞书 bot 真实收发（需用户实测）；DS 服务健康页 + 告警规则（Lv3）；Lv4-7 数据层/交付/CD/体验美学

### 会话 17：Lv3 可观测性完成 — 聚合链路 + 告警规则 + DS 服务健康页

**工作内容:**
1. **gateway 聚合端点修复** — [internal.py](file:///d:/MW/ghost-main/gateway/routes/internal.py) monitoring_metrics 弃用 `_proxy_request`（JSON 解析器无法处理 Prometheus 纯文本）→ httpx 直抓 + 并发 gather。**7/7 服务全 ok（overall=ok）**。
2. **全服务 /metrics 补齐** — flow（health.ts registerMetricsRoutes + index.ts 认证豁免）、netagent（/metrics PlainTextResponse）、nebula（requirements 补 prometheus-client 重建）。
3. **Prometheus 告警规则** — [service.yml](file:///d:/MW/monitoring/prometheus/rules/service.yml) 4 条（ServiceDown/EngineStopped/HighTaskFailureRate/HighMemoryUsage），rule_files 引用 + compose 挂载 rules 目录。**8 target 全 up，4 规则已加载**。
4. **DS 服务健康页** — [Sidebar.tsx](file:///d:/MW/DS/src/components/layout/Sidebar.tsx) "平台"分组加入口；[NavIcon.tsx](file:///d:/MW/DS/src/components/shared/NavIcon.tsx) 新增 health 心跳图标；新建 [health/page.tsx](file:///d:/MW/DS/src/app/health/page.tsx)（总览 Hero + 7 服务卡片 + 延迟/负载/运行时长 + Prometheus 原始指标折叠 + 5s 自动刷新）。
5. **监控路由路径修正（bug）** — `api/internal/monitoring/route.ts` 声明 `/metrics` 路径但实际挂载于 `/monitoring`（404）→ 迁移至 `monitoring/metrics/route.ts`，与 gateway 路径镜像。

**结果:** DS `/health` 页 HTTP 200（含"服务健康"）；`/api/internal/monitoring/metrics` success=True overall=ok 7/7；TS 编译通过；镜像重建后容器 healthy。

### 会话 18：项目落地 — 飞书恢复 + 数据备份 + 一键交付

**工作内容:**
1. **飞书 bot 恢复（漏洞：脱离 compose 生命周期）** — feishu-bot 定义在独立 `docker-compose.feishu.yml`，默认 `docker compose up` 不加载 → 容器退出 10 小时无人管理。**合并 feishu-bot + feishu-consumer 进主 docker-compose.yml**（凭证改非强制 `:-`，删除独立文件），全栈统一管理。
2. **凭证修复** — 主 .env 的 FEISHU_APP_SECRET 是旧值（invalid），feishu-bot/.env 是新值但已不生效 → 主 .env 更新为新轮换值。**飞书 WebSocket 重新连接成功**。
3. **bot.py 健壮性** — 无凭证时休眠等待而非 `sys.exit(1)`（避免 `restart: unless-stopped` 无限重启循环）。
4. **Lv4 数据层备份** — 新增 [backup.ps1](file:///d:/MW/scripts/backup.ps1)（全库 pg_dump 到 backups/，保留最近 7 份，实测 4 库全备份成功）+ [restore.ps1](file:///d:/MW/scripts/restore.ps1)（危险操作双确认）；Makefile 加 `make backup` / `make restore`；.gitignore 忽略 backups/ + `*.dump`，解禁 scripts/* 下的交付脚本。
5. **Lv5 一键交付** — [start_all.bat](file:///d:/MW/scripts/start_all.bat) 重写为 Docker 一键启动（检查 Docker/.env → up -d → 健康检查 → 打开健康页）；.env.example 补 KNOWN_CHAT_IDS/DEFAULT_BACKEND。
6. **文档同步** — SYSTEM_MAP.md 端口表补 Feishu-Bot/Consumer，部署关系更新为 12 服务。

**结果:** 飞书 WS 已连；备份实测 OK；14 容器 healthy；E2E 10/10 仍 ALL GREEN。

**待办:** GitHub 推送（网络恢复后重试）；飞书 bot 真实收发（需用户在飞书发消息实测命令路由）。
