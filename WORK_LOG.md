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
- 修复 doubao/human chat 测试（筛选目标 URL 跳过 login 调用）
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

## 待办

- [x] Docker Desktop 启动后验证全栈健康
- [x] 逐步接入 Alpha-ID 新模块到 Gateway 路由（brain/voice/social）
- [ ] 为 Nebula、Alpha-ID 补充单元测试
- [ ] 接入真实 ToolA/ToolB 服务（替换 stub）
- [x] DS 添加 demo seed script 验证
- [x] Alpha-ID GhostBrain/GhostVoice 接入 Gateway 路由
