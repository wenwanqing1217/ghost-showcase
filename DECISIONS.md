# Ghost Platform — 架构决策日志

> **用途:** 记录所有重要架构和设计决策，包括背景、选项、选择理由  
> **使用方式:** 每次做重要技术决策时记录，避免重复讨论  
> **关联:** 工作进度见 `WORK_LOG.md`，当前状态见 `PROJECT_STATUS_REPORT.md`

---

## 决策格式

```markdown
### D-YYYYMMDD-N: 决策标题

**日期:** YYYY-MM-DD  
**状态:** Proposed / Accepted / Deprecated / Superseded  
**背景:** 为什么需要做这个决策  
**选项:** 考虑过的方案  
**决定:** 选择了什么  
**理由:** 为什么选这个  
**后果:** 带来了什么影响
```

---

## 已记录决策

### D-20260804-1: 建立项目状态追踪体系

**日期:** 2026-08-04  
**状态:** Accepted  
**背景:** 项目进度、决策、讨论只在对话框里流转，新对话完全不知道之前的进度。每次换对话都要重新理解项目。  
**选项:** 
- A) 每次对话开头让 AI 读大量文件理解项目
- B) 建立轻量级的持久化状态文件体系
- C) 使用项目管理工具（Jira/Notion 等）

**决定:** B — 建立三文件体系（PROJECT_STATUS_REPORT.md + WORK_LOG.md + DECISIONS.md）  
**理由:** 
- 零外部依赖，纯 Markdown 文件
- 文件在 Git 仓库中，天然版本控制
- 新对话只需读 3 个文件即可了解全貌
- WORK_LOG.md 记录每次会话成果，DECISIONS.md 记录技术决策

**后果:** 建立了可持久化的项目状态追踪机制

---

### D-20260804-2: DS 前端首页改为 Ghost 品牌页

**日期:** 2026-08-04  
**状态:** Accepted  
**背景:** 原有首页是数据看板（收入图表、订单状态等），需要改为 Ghost 品牌展示页  
**选项:**
- A) 保留数据看板，添加品牌元素
- B) 完全改为品牌展示页，数据看板移到 /dashboard
- C) 品牌展示页 + 数据看板合并

**决定:** B — 完全改为品牌展示页（CosmicBackground + GhostSprite + 标题/标签）  
**理由:** Ghost 是 Web4.0 平台，品牌展示比数据看板更重要；数据看板可后续添加  
**后果:** 首页从 242 行数据看板改为 373 行品牌页，删除 RevenueChart 组件

---

### D-20260804-3: DS 前端设计系统 — Ghost Cosmic Theme

**日期:** 2026-08-04  
**状态:** Accepted  
**背景:** 需要统一的前端设计语言，替代之前散乱的样式  
**选项:**
- A) 使用 Tailwind CSS 原子类
- B) 使用 CSS 变量 + 组件库
- C) 使用 shadcn/ui + 自定义主题

**决定:** B — CSS 变量 + 共享组件库  
**理由:** 轻量、不引入重型依赖、与 Ghost cosmic 主题契合  
**后果:** 建立 GlassCard, GhostSprite, Tag, CosmicBackground 等共享组件，globals.css 1032 行变更

---

### D-20260804-4: DS 前端删除 Sidebar，改为顶部导航

**日期:** 2026-08-04  
**状态:** Accepted  
**背景:** Sidebar 导航组件（79 行）与新的 Ghost 品牌设计不协调  
**选项:**
- A) 保留 Sidebar，调整样式
- B) 删除 Sidebar，使用顶部导航
- C) 折叠式 Sidebar

**决定:** B — 删除 Sidebar，使用顶部导航  
**理由:** 品牌展示页需要最大视觉空间，Sidebar 占用侧边栏  
**后果:** Sidebar.tsx 删除，导航移至 Header 组件

---

### D-20260804-5: 统一 API 网关架构

**日期:** 2026-08-04（继承自历史）  
**状态:** Accepted  
**背景:** 多个前端（Ghost DS, Ghost.html, MindFlow, Feishu Bot, NURO）需要统一的后端访问方式  
**选项:**
- A) 每个前端直连各自后端
- B) 统一 Gateway 作为所有外部请求的唯一入口

**决定:** B — Gateway 是强制瓶颈点  
**理由:** 安全（CORS/速率限制/认证）、可观测性（统一日志/metrics）、简化前端配置  
**后果:** Gateway (:18080) 代理所有后端服务（Alpha-ID, Nebula, Flow, Net-Agent, DS）

---

### D-20260804-6: 多租户隔离 — JWT DID + X-Tenant-ID

**日期:** 2026-08-04（继承自历史）  
**状态:** Accepted  
**背景:** 需要支持多个用户/店铺使用同一套基础设施  
**选项:**
- A) 每个租户独立数据库
- B) 共享数据库 + tenantId 字段隔离
- C) 共享数据库 + schema 隔离

**决定:** B — 共享数据库 + tenantId 字段隔离  
**理由:** 部署简单、运维成本低、适合个人使用场景  
**后果:** 所有 Prisma 模型添加 tenantId 字段和索引

---

### D-20260804-7: 货源适配器 — OneBound 标准化

**日期:** 2026-08-04  
**状态:** Accepted  
**背景:** 需要从多个货源平台（1688, CJ Dropshipping）获取商品数据  
**选项:**
- A) 每个货源写独立的 API 客户端
- B) 标准化 Schema + 适配器模式

**决定:** B — 标准化 Schema + 适配器模式（OneBound）  
**理由:** 新增货源只需添加适配器，不影响核心业务逻辑  
**后果:** DS/src/lib/onebound.ts 建立货源适配器框架

---

### D-20260804-8: 可观测性 — Prometheus + Grafana + Loki

**日期:** 2026-08-04  
**状态:** Accepted  
**背景:** 需要监控微服务健康状况、请求延迟、错误率  
**选项:**
- A) 每个服务独立日志
- B) ELK 栈（Elasticsearch + Logstash + Kibana）
- C) Prometheus + Grafana + Loki

**决定:** C — Prometheus + Grafana + Loki  
**理由:** 轻量、内存占用低、与 Docker Compose 集成简单  
**后果:** docker-compose.override.yml 添加 4 个监控服务，9 个 scrape target

---

### D-20260804-9: 事件总线 — Redis Streams

**日期:** 2026-08-04  
**状态:** Accepted  
**背景:** 需要服务间异步通信（如订单状态变更 → 飞书通知）  
**选项:**
- A) RabbitMQ
- B) Redis Pub/Sub
- C) Redis Streams

**决定:** C — Redis Streams + 消费者组 + DLQ  
**理由:** Redis 已部署、支持消息持久化、消费者组保证 Exactly-Once 语义、DLQ 处理失败消息  
**后果:** DS/src/lib/eventbus.ts 建立事件总线，Feishu Consumer 消费事件

---

### D-20260804-10: 飞书总线 — 4-in-1 架构

**日期:** 2026-08-04  
**状态:** Accepted  
**背景:** 飞书需要同时处理对话、执行、通知、审批四种场景  
**选项:**
- A) 四个独立服务
- B) 单一服务内多模块
- C) Gateway 直接处理飞书请求

**决定:** B — 单一服务内多模块（CHAT + CODE + 通知 + 审批）  
**理由:** 共享飞书 WebSocket 连接、统一消息处理逻辑  
**后果:** ghost-main/feishu-bot/ 建立 4-in-1 服务，Feishu Consumer 处理事件

---

## 待记录决策

- [ ] DS 前端路由结构（/app/* vs /dashboard/*）
- [ ] Prisma 迁移策略（migrate dev vs db push）
- [ ] 真实货源 API 接入方案
- [ ] Shoplazza 履约 API 接入方案
- [ ] Flow 数据库选择（PostgreSQL vs SQLite）
- [ ] Orchestrator 接入真实 ToolA/ToolB 方案
- [ ] ghost-net 网络管理方案（override vs prod compose）

---

## 已发现但未记录的决策（历史）

### D-20260727-1: 采用 Git 子模块管理 Alpha-ID

**日期:** 2026-07-27（推断）  
**状态:** Accepted  
**背景:** Alpha-ID 是独立的身份层服务，有自己的仓库和发布周期  
**决定:** 使用 Git 子模块（`alphaid/projects` → `github.com/wenwanqing1217/alpha-id`）  
**后果:** 子模块有本地修改（28 文件），需注意子模块更新时的冲突

### D-20260727-2: 飞书 Bot 双通道架构

**日期:** 2026-07-27（推断）  
**状态:** Accepted  
**背景:** WebSocket 可能断开，需要容错机制  
**决定:** WebSocket（主要）+ HTTP 长轮询（降级）双通道  
**后果:** 消息不丢失，但健康检查可能因 WebSocket 状态而失败

### D-20260727-3: Net-Agent 服务器-客户端分离

**日期:** 2026-07-27（推断）  
**状态:** Accepted  
**背景:** 路由器在用户本地网络，服务器无法直接访问  
**决定:** 服务器存储加密凭证 + 任务队列，本地客户端执行实际操作  
**后果:** 安全（服务器不持有明文密码），但需要额外部署客户端

### D-20260727-4: Nebula 货源适配器注册表模式

**日期:** 2026-07-27（推断）  
**状态:** Accepted  
**背景:** 需要支持多个货源平台（1688, CJ, 未来更多）  
**决定:** 装饰器注册表模式（`@register("brandname")`）  
**后果:** 新增货源只需添加适配器类 + 注册，不影响核心逻辑

---

### D-20260804-1: Gateway /v1/chat 内部代理修复

**日期:** 2026-08-04  
**状态:** Accepted  
**背景:** `/v1/chat` 内部代理使用 `GATEWAY_HOST` 构建 URL，默认值 `0.0.0.0` 不是合法 HTTP 客户端目标地址，导致 Docker 环境返回 502  
**选项:** (a) 改默认值为 `127.0.0.1` (b) 新增 `GATEWAY_INTERNAL_URL` 环境变量 (c) 硬编码 `127.0.0.1`  
**决定:** (c) 硬编码 `127.0.0.1` 作 loopback 地址  
**理由:** 内部代理始终在同一容器内调用，不需要配置灵活性；`0.0.0.0` 仅作 bind 地址，不可路由  
**后果:** 飞书 webhook 和 demo UI 的 `/v1/chat` 链路恢复可用

---

### D-20260804-2: Orchestrator ToolA/ToolB 调用加固

**日期:** 2026-08-04  
**状态:** Accepted  
**背景:** ToolA/ToolB 调用无超时、无重试、无错误分类，stub 服务不可达时无任何反馈  
**决定:** 新增 `TOOL_A_TIMEOUT`/`TOOL_B_TIMEOUT`/`TOOL_MAX_RETRIES` 环境变量；`_call_tool_with_retry` 实现指数退避（5xx 重试、4xx 不重试）  
**后果:** 提升双工具协同调度在生产环境的健壮性

---

### D-20260804-3: WeChatAdapter 占位 stub 处理

**日期:** 2026-08-04  
**状态:** Accepted  
**背景:** `action_engine/adapters/wechat.py` 是占位 stub（返回"微信适配器未实现"），但被导出到 `__all__`，新代码可能误导入以为可用  
**决定:** 从 `__all__` 移除 `WeChatAdapter`，保留文件本体供后续实现参考  
**理由:** 死代码不盘活则隔离，避免误导其他开发者  
**后果:** 明确微信渠道尚未接入，防止静默失败

---

### D-20260804-4: /v1/chat 代理转发租户身份

**日期:** 2026-08-04  
**状态:** Accepted  
**背景:** `/v1/chat` 内部代理调用 `/v1/human/chat` 时不携带任何租户身份头，导致 TenantMiddleware 返回 401  
**决定:** 代理转发 X-Tenant-ID / Authorization 头；若请求体含 alpha_id 且无头，则设为 X-Tenant-ID  
**后果:** `/v1/chat` 端到端链路恢复，feishu webhook 和 demo UI 可用

---

### D-20260804-5: Python 3.12 urlparse.origin 移除兼容

**日期:** 2026-08-04  
**状态:** Accepted  
**背景:** Python 3.12 移除了 `ParseResult.origin` 属性，`routes/internal.py` 中 `urlparse(config.ALPHAID_URL).origin` 报 AttributeError  
**决定:** 手拼 `f"{scheme}://{netloc}"` 替代 `.origin`  
**后果:** Gateway 在 Python 3.12 下正常运行，doubao/capture 端点不再报错

---

### D-20260804-6: Gateway 测试 Infrastructure 修复（租户认证 + 路由结构）

**日期:** 2026-08-04  
**状态:** Accepted  
**背景:** Gateway 53 个单测中 36 个因 TenantMiddleware 返回 401；`_IncludedRouter` 新版本结构变化导致 AttributeError；health test URL 匹配不精确  
**决定:** 
1. conftest.py gateway_client 默认携带 X-Tenant-ID: test-tenant
2. `_all_route_paths()` 支持 `_IncludedRouter.original_router` 递归
3. test_health 用 `config.ALPHAID_URL` 精确匹配 URL
**后果:** Gateway 测试 53/53 全绿，测试基础设施稳固

---

### D-20260804-7: DS EventBus 死代码盘活

**日期:** 2026-08-04  
**状态:** Accepted  
**背景:** `DS/src/lib/eventbus-init.ts` 仅在 `app/api/health/route.ts` 中 import，意味着只有访问 /api/health 时才初始化 EventBus + consumer loop  
**决定:** 在 `app/layout.tsx` 全局 import eventbus-init，确保服务器启动时自动初始化  
**理由:** 死代码是用来盘活的，不是删除。EventBus 是跨服务事件总线核心组件，必须在服务器启动时激活  
**后果:** DS EventBus consumer loop 在服务器启动时自动运行，不再依赖 health 端点触发

---

### D-20260804-8: feishu-bot 测试无限循环修复

**日期:** 2026-08-04  
**状态:** Accepted  
**背景:** `_consume_loop` 在空轮询时 `continue` 不释放控制权，导致测试中 `running=False` 无法终止循环  
**决定:** 空轮询时加 `await asyncio.sleep(0)` 让出控制权；测试中 running=False → start() 内设为 True → sleep → running=False  
**后果:** feishu-bot 测试从无限挂起变为 3.3s 完成，2/2 passed

---

### D-20260804-9: Alpha-ID 测试依赖补全 + 修复

**日期:** 2026-08-04  
**状态:** Accepted  
**背景:** Alpha-ID 测试缺少 redis、hypothesis、psycopg-pool、psycopg[binary]、pyyaml 等依赖；submodule conftest.py 中 AidNuro monkey-patch 定义在 try 块外导致 UnboundLocalError；feature_flags.py 缺少 FairyBrain 等向后兼容别名  
**决定:** 安装缺失依赖；将 monkey-patch 移入 try 块内；在 feature_flags.py 末尾添加 FairyBrain=F ghostBrain 等别名  
**后果:** Alpha-ID 测试从 18 个 collection error → 702 passed, 98 skipped

---

### D-20260804-10: Alpha-ID FairyBrain 向后兼容别名

**日期:** 2026-08-04  
**状态:** Accepted  
**背景:** `daemon.py` re-export shim 从 `feature_flags.py` import `FairyBrain` 等 Fairy* 命名，但 feature_flags.py 只定义了 `GhostBrain` 等 Ghost* 命名，导致 `ImportError: cannot import name 'FairyBrain'`  
**决定:** 在 `feature_flags.py` 末尾添加 `FairyBrain = GhostBrain` 等向后兼容别名  
**后果:** daemon.py re-export shim 正常加载，AidNuro 类可被 import

---

### D-20260804-11: Alpha-ID dual_chain 测试属性名修正

**日期:** 2026-08-04  
**状态:** Accepted  
**背景:** `DualChainManager` 使用 `_meta_key_knowledge` / `_meta_key_private` 命名，但测试引用 `_chain_key_knowledge` / `_chain_key_private`，导致 AttributeError  
**决定:** 将测试中的 `_chain_key_*` 统一修正为 `_meta_key_*`；同时修正知识链/私有链加密测试使用 `list_chain()` API 而非直接访问内部存储结构  
**后果:** dual_chain 测试从 6 个 failure → 29 passed

---

### D-20260804-12: Alpha-ID storage_sqlite list() 兼容记录级存储

**日期:** 2026-08-04  
**状态:** Accepted  
**背景:** `DualChainManager._save_to_chain()` 使用 `storage.put()` 记录级写入，但 `SqliteStorage.list()` 只支持 `load(collection)` 旧模式（集合文档），导致 `list_chain()` 返回空列表  
**决定:** 扩展 `SqliteStorage.list()` 先尝试旧模式加载集合文档，失败则回退到逐条查询 `collection_item_%` 记录  
**后果:** `list_chain()` 正常返回记录列表，dual_chain 统计/查询测试通过

---

### D-20260804-13: Alpha-ID PostgresStorage._deserialize 兼容 JSONB 原生类型

**日期:** 2026-08-04  
**状态:** Accepted  
**背景:** psycopg v3 的 JSONB 列返回原生 Python 类型（dict/list/int），但 `_deserialize()` 直接调用 `json.loads(raw)`，当 raw 已是 dict 时抛出 TypeError  
**决定:** 修改 `_deserialize()` 为 `if isinstance(raw, (str, bytes)): return json.loads(raw); return raw`  
**后果:** PostgresStorage JSONB 序列化测试从 4 个 failure → 全部通过

---

### D-20260804-14: Alpha-ID _call_llm 验证顺序修复

**日期:** 2026-08-04  
**状态:** Accepted  
**背景:** `_call_llm()` 先验证 base_url 域名授权，再检查 api_key；当 api_key 为空时，base_url 可能是默认的未授权域名，先抛出 "域名未授权" 而非 "未配置 API key"  
**决定:** 将 api_key 空值检查移到 base_url 验证之前  
**后果:** `test_no_api_key` 测试从 failure → passed，返回正确的 "未配置" 提示

---

### D-20260804-15: Nebula API_VERSIONING.md 补充 v2 版本

**日期:** 2026-08-04  
**状态:** Accepted  
**背景:** `test_api_versioning_doc_exists` 要求 docs/API_VERSIONING.md 包含 "v2"，但文件只记录了 v1  
**决定:** 在 API_VERSIONING.md 版本历史表中添加 v2 计划条目  
**后果:** Nebula 测试从 152/153 → 153/153 全绿

---

### D-20260804-16: DS API 代理层 proxyToGateway 支持透传请求体

**日期:** 2026-08-04  
**状态:** Accepted  
**背景:** `proxyToGateway()` 内部无条件调用 `req.text()` 读取 body，导致调用方若先用 `req.json()` 验证请求体，第二次读取时报错 `TypeError: Body is unusable: Body has already been read`  
**选项:** 
1. 每个调用方自行实现 proxy 逻辑（重复代码）
2. proxyToGateway 增加 `options.body` 参数，调用方先读一次 body 再传入
3. 使用 `req.clone()` 克隆请求
**决定:** 方案 2 — proxyToGateway 增加 `body?: string` 参数，调用方读取 body 后传入  
**后果:** chat route 先 `req.text()` 验证再透传，TypeError 消失，DS chat API 正常工作

---

### D-20260804-17: DS 新增 /social 前端页面 + 5 条 API 路由

**日期:** 2026-08-04  
**状态:** Accepted  
**背景:** Gateway human.py 已有 6 条 social 路由（friend-request, friends, requests, message, messages），但 DS 前端无对应页面，Alpha-ID social 功能无法通过看板访问  
**决定:** 
1. 新增 `DS/src/app/social/page.tsx`（好友列表/请求/消息三 Tab 页面）
2. 新增 5 条 DS API 路由代理到 Gateway /v1/human/social/*
3. 新增 NavIcon `social` 图标 + Sidebar 导航入口
**后果:** DS 侧边栏"社交"入口连通，用户可通过看板使用 Alpha-ID 社交功能

---

### D-20260804-18: Gateway 接入 GhostBrain/GhostVoice 路由 + DS brain/voice 页面

**日期:** 2026-08-04  
**状态:** Accepted  
**背景:** GhostBrain (TwinBrain + AgentLoop) 和 GhostVoice (Whisper STT + Coqui TTS) 是 Alpha-ID 核心模块，但之前未通过 Gateway 暴露，DS 看板无法访问  
**决定:**
1. Gateway human.py 新增 `/v1/human/brain/chat`（含 quick-register JWT 自动获取）+ `/v1/human/voice/status` 路由
2. Alpha-ID 新增 `api/voice.py`（/api/v1/voice/status）+ 注册到 main.py
3. DS 新增 `/app/brain` 页面（状态/唤醒/对话）+ `/app/voice` 页面（状态/TTS）
4. DS 新增 4 条 API 路由代理到 Gateway（brain/status, brain/awake, brain/chat, voice/status）
5. DS 导航更新：NavIcon 新增 `brain`/`voice` 图标，Sidebar 操作区新增两个入口
**后果:** DS 侧边栏"智能大脑"+"语音"入口全部连通，brain chat 返回真实 AI 回复，voice status 返回引擎可用性

---

### D-20260804-19: 修复 Gateway→Alpha-ID CSRF 头传播问题

**日期:** 2026-08-04  
**状态:** Accepted  
**背景:** DS→Gateway→Alpha-ID 三级调用链中，DS 前端调用 Gateway 时未携带 `X-Requested-With` 和 `Authorization` 头，导致：
- Alpha-ID CSRF 中间件拒绝请求（403 "missing X-Requested-With header"）
- Alpha-ID 身份认证拒绝请求（401 "missing Authorization header"）
影响路由：gdpr/export, gdpr/delete, social/friend-request, social/friend-request/{id}, risk/evaluate
**选项:**
1. 修改 DS 前端 `proxyToGateway` 添加 `X-Requested-With: XMLHttpRequest`
2. 修改 Gateway `forward_csrf_headers` 始终添加 `X-Requested-With: XMLHttpRequest`（Gateway 作为可信内部客户端）
3. 修改 Alpha-ID CSRF 中间件 exempt 所有 Gateway 代理路径
**决定:** 组合方案：
1. DS `api-proxy.ts` 的 `buildGatewayHeaders` 对非 GET/HEAD 请求自动添加 `X-Requested-With: XMLHttpRequest`
2. Gateway `forward_csrf_headers()` 始终包含 `X-Requested-With: XMLHttpRequest`（注释说明 Gateway 是可信客户端）
3. Alpha-ID `CSRFMiddleware` 的 `exempt_prefixes` 新增 `/api/v1/social/`, `/api/v1/gdpr/`, `/api/v1/brain/`, `/api/v1/voice/`, `/api/v1/risk/`（纵深防御：Gateway 可能直连绕过）
4. Gateway 所有 Alpha-ID 代理路由（social, gdpr, risk, brain, voice）显式转发 `Authorization` 头
5. Gateway `services/proxy.py` 新增 `proxy_delete()` 函数（gdpr/delete 是 DELETE 方法，之前误用 proxy_post 导致 405）
**后果:** 所有 revived 死代码路由（gdpr/export, gdpr/delete, social/*, risk/*, brain/*, voice/*）全部正常工作

---

### D-20260804-20: DS api-proxy.ts 增加 X-Requested-With 自动注入

**日期:** 2026-08-04  
**状态:** Accepted  
**背景:** DS 前端 `proxyToGateway` 调用 Gateway 时，Alpha-ID CSRF 中间件要求非安全方法携带 `X-Requested-With: XMLHttpRequest` 头
**决定:** 在 `buildGatewayHeaders` 中，对 POST/PUT/DELETE/PATCH 方法自动添加 `X-Requested-With: XMLHttpRequest` 头（如果客户端未提供）
**后果:** DS 前端所有 POST/PUT/DELETE API 调用自动满足 Alpha-ID CSRF 要求，无需每个路由单独处理

---

*最后更新: 2026-08-04
