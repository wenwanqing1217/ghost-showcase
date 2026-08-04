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

*最后更新: 2026-08-04*
