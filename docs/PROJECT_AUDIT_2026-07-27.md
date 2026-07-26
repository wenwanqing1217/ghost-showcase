# Ghost 项目全景审计报告

> **审计日期**: 2026-07-27  
> **审计范围**: 全部 392 个 .py、61 个 .md、38 个 .ts、35 个 .js、20 个 .tsx 及所有配置/脚本  
> **审计方法**: 15 路并行初扫 + 6 路深度审查 + GitHub 对标研究  
> **审计标准**: OWASP Top 2021、FastAPI 最佳实践、NIST 密码学标准、GitHub 顶级开源项目

---

## 📋 执行摘要

| 维度 | 评分 | 说明 |
|------|------|------|
| 架构设计 | 6.5/10 | 独创设计多（双链记忆、TwinBrain、Gateway 三层路由），但重复代码多 |
| 安全性 | 4.5/10 | demo 模式泄露、私钥明文返回、JWT 弱派生、时序攻击风险 |
| 代码质量 | 5.5/10 | DRY 违反（规则引擎×2、Base×2、AuthProvider×2），全局单例泛滥 |
| 生产就绪度 | 5/10 | 缺集成测试、DB 迁移脆弱、监控自实现 |
| 文档健康度 | 4/10 | 52 个 .md 中 4 份严重重叠，数字与代码不符 |
| **综合** | **5.3/10** | **功能丰富的 MVP，距离生产级需系统性的安全加固和代码整理** |

**一句话评价**: 你能写东西，也能设计，但项目的"熵"太高——重复代码、冗余文档、散落的一次性脚本让维护成本居高不下。

---

## 🏗️ 系统架构全景

### 服务地图

```
                              用户入口
                    ┌──────────┼──────────┐
                    ▼          ▼          ▼
              Ghost.html   飞书 Bot   桌面 FAIRY
              (A2A+Mindflow)  │      (Tkinter+Ollama)
                    │          │          │
                    └──────────┼──────────┘
                               ▼
                    ┌─────────────────────┐
                    │   Gateway (:18080)  │
                    │ /v1/human /v1/agent │
                    │ /v1/internal        │
                    └──┬──────┬──────┬────┘
                       │      │      │
          ┌────────────┘      │      └────────────┐
          ▼                   ▼                   ▼
   Alpha-ID (:8000)    Nebula (:2002)      Orchestrator (:19090)
   身份+Agent+记忆      MindFlow Map         ⚠️ PoC 骨架
          │                   │
          │                   ├──→ Flow (:3001) ❌ 源码缺失
          │                   └──→ DS (:3004)   ✅ Shoplazza 电商
          │
          ├──→ Net-Agent (:18180)  ──→ 路由器管理 (OpenWrt/小米/TP)
          ├──→ Doubao Reader       ──→ LevelDB 解析 → Obsidian
          ├──→ Collector Daemon    ──→ Cursor/Trae/Git 活动采集
          └──→ FAIRY Desktop Pet ──→ 本地 AI 桌面精灵


   数据采集层
   ┌──────────────────────────────────────────────────────────┐
   │ 豆包网页版 ──(Chrome 扩展 content.js)──→ Gateway          │
   │ 豆包桌面版 ──(LevelDB 解析)──────────→ Reader → Obsidian │
   │ 飞书消息   ──(feishu-bot)───────────→ CLI 后端           │
   │ 路由器     ──(net_client)───────────→ net_agent_server   │
   │ 开发工具   ──(collector_daemon)────→ Gateway             │
   └──────────────────────────────────────────────────────────┘
```

### 端口分配

| 端口 | 服务 | 状态 | 用途 |
|------|------|------|------|
| 8000 | Alpha-ID API | ✅ 运行 | 身份 + 双链记忆 + Agent 对话 |
| 18080 | Gateway | ✅ 运行 | 三层路由 + 统一信封 |
| 2002 | Nebula (MindFlow) | ✅ 已验证 | 地图 + 工作流 + 审批 + 自动化 |
| 3001 | Flow | ❌ **源码缺失** | 工作流引擎（空壳） |
| 3004 | DS (Ghost DS) | ✅ 完整可运行 | Shoplazza 电商看板 |
| 18180 | Net-Agent Server | ✅ 运行 | 路由器远程管理 |
| 19090 | Orchestrator | ⚠️ PoC 骨架 | 任务调度（ToolA/ToolB 模拟） |
| 11434 | Ollama (外部) | ✅ 依赖 | FAIRY 本地推理 |
| 5432 | PostgreSQL (外部) | 🟡 可选 | 生产数据库 |
| 6379 | Redis (外部) | 🟡 已编码未声明 | 缓存 + 限流后端 |

---

## 🔴 第一优先级：安全红线（立即修复）

### S1 — DID 私钥明文返回

| 项目 | 详情 |
|------|------|
| 文件 | `alphaid/projects/src/api/registration.py:239` |
| 代码 | `"privateKey": signer.export_private_key().hex()` |
| 风险 | 用户注册时服务器返回完整私钥，任何中间人/日志系统可窃取 |
| 修复 | 私钥仅客户端生成并存储，服务器只接收公钥/DID |
| 参考 | [didkit](https://github.com/spruceid/didkit) — 密钥永不离开客户端 |

### S2 — Face Verify 完全信任客户端

| 项目 | 详情 |
|------|------|
| 文件 | `alphaid/projects/src/api/registration.py:190-201` |
| 代码 | 不验证签名即返回 `passed: True` |
| 风险 | 任意用户可构造 certify_id 通过人脸认证 |
| 修复 | 服务端验证签名 + 比对人脸特征哈希 |

### S3 — JWT 密钥派生使用 SHA-256 而非 HKDF

| 项目 | 详情 |
|------|------|
| 文件 | `alphaid/projects/src/auth/jwt.py:28-30` |
| 代码 | `return hashlib.sha256(raw).digest()` |
| 风险 | 若 AUTH_MASTER_KEY 熵不足（如 `mysecret123`），签名密钥脆弱 |
| 修复 | 使用 `HKDF-SHA256` 或直接要求 32-byte 随机密钥 |
| 参考 | [PyJWT 最佳实践](https://pyjwt.readthedocs.io/en/latest/usage.html) |

### S4 — SMS Demo 模式默认开启且返回验证码

| 项目 | 详情 |
|------|------|
| 文件 | `alphaid/projects/src/api/registration.py:85-124` |
| 代码 | `SMS_DEMO_MODE=true` 时直接返回 `"demo": code` |
| 风险 | 任何人可通过注册接口获取任意手机号的验证码 |
| 修复 | Demo 模式改为仅输出日志不返回；生产环境强制关闭 |

### S5 — 飞书 Webhook Token 时序攻击

| 项目 | 详情 |
|------|------|
| 文件 | `nebula/src/mindflow_map/api/feishu_webhook.py:35` |
| 代码 | `token != settings.feishu_verification_token` |
| 风险 | 普通 `!=` 比较存在时序旁路攻击风险 |
| 修复 | 改用 `hmac.compare_digest()` |

### S6 — 密码明文存储在配置中

| 项目 | 详情 |
|------|------|
| 文件 | `nebula/src/mindflow_map/config.py:95` |
| 代码 | `douyin_password: str = ""` |
| 风险 | `.env` 文件中的密码以明文形式加载到内存 |
| 修复 | 使用 `SecretStr` 类型 + 运行时解密 |

### S7 — 限流仅按 IP，不识别代理后客户端

| 项目 | 详情 |
|------|------|
| 文件 | `nebula/src/mindflow_map/middleware/rate_limit.py:45` |
| 代码 | `client_id = request.client.host or "unknown"` |
| 风险 | 反向代理（Nginx/Caddy）后所有请求看起来来自同一 IP |
| 修复 | 优先读取 `X-Forwarded-For` / `X-Real-IP` 头 |

### S8 — 根目录私钥文件

| 项目 | 详情 |
|------|------|
| 文件 | `D:\MW\alipay_private_pkcs1.pem` |
| 风险 | 私钥直接存放在仓库根目录，可能被误提交到 Git |
| 修复 | 移动到安全存储（Vault/外部目录），加入 `.gitignore` |

---

## 🟡 第二优先级：功能缺陷（本周修复）

### F1 — daemon.py 引用不存在的类

| 项目 | 详情 |
|------|------|
| 文件 | `alphaid/projects/src/entrypoints/daemon.py:1400` |
| 代码 | `AIDFairy(...)` — 实际类名为 `AidNuro` |
| 影响 | 桌面精灵入口启动即崩溃（NameError） |

### F2 — Nebula 引用不存在的微信模块

| 项目 | 详情 |
|------|------|
| 文件 | `nebula/src/mindflow_map/api/events.py:193` |
| 代码 | `from mindflow_map.api.wechat import _parse_xml` |
| 影响 | 启动时 ImportError |

### F3 — 向量嵌入无语义能力

| 项目 | 详情 |
|------|------|
| 文件 | `alphaid/projects/src/core/memory_store.py` `_SimpleEmbeddingFunction` |
| 问题 | 字符级 n-gram + MD5 哈希，"苹果"和"apple"完全不同 |
| 影响 | 记忆检索无法语义匹配 |
| 修复 | 启用 ChromaDB 内置 ONNX MiniLM 或 BGE-small-zh |

### F4 — AgentLoop 每次请求新建实例，无对话历史

| 项目 | 详情 |
|------|------|
| 文件 | `alphaid/projects/src/api/agent.py:12` |
| 问题 | 每次 `/chat` 创建新 AgentLoop，history 不持久化 |
| 影响 | 多轮对话无法记忆上文 |

### F5 — TwinBrain 同步/异步双版本维护成本高

| 项目 | 详情 |
|------|------|
| 文件 | `alphaid/projects/src/core/twin_brain.py` |
| 问题 | `receive()` 和 `areceive()` 几乎相同逻辑 |

### F6 — 规则引擎重复（2 处）

| 项目 | 详情 |
|------|------|
| 文件 | `nebula/src/mindflow_map/ai/fallback_rules.py` + `workflows/engine.py:556-632` |
| 问题 | 同一份关键词匹配逻辑存在两处 |

### F7 — 两个不同的 SQLAlchemy Base

| 项目 | 详情 |
|------|------|
| 文件 | `nebula/src/mindflow_map/models/database.py` + `memory/store.py` |
| 问题 | alembic 迁移只覆盖部分表 |

### F8 — 中间件顺序错误

| 项目 | 详情 |
|------|------|
| 文件 | `nebula/src/mindflow_map/main.py:105-135` |
| 当前 | CORS → Audit → Auth → RateLimit → Prometheus → CorrelationId |
| 应改为 | CorrelationId → CORS → Prometheus → RateLimit → Auth → Audit |

---

## 🟢 第三优先级：代码质量（持续改进）

### Q1 — 重复造轮子清单

| 自实现 | 文件 | 推荐替代 | Stars |
|--------|------|----------|-------|
| `MetricsRegistry` | `nebula/core/metrics.py` | [prometheus-fastapi-instrumentator](https://github.com/trallnag/prometheus-fastapi-instrumentator) | ⭐2.1k |
| `EventQueue` | `nebula/core/events.py` | [arq](https://github.com/python-arq/arq) (async Redis) | ⭐2.3k |
| `CircuitBreaker` | `nebula/ai/circuit_breaker.py` | [pybreaker](https://github.com/danielmesquitta/pybreaker) | ⭐1.5k |
| `InMemoryCache`+`RedisCache` | `nebula/core/cache.py` | [cachetools](https://github.com/tkem/cachetools) + redis | ⭐2.2k |
| `AuthProvider` 双份 | `nebula/core/auth.py`+`models/auth_store.py` | [fastapi-users](https://github.com/fastapi-users/fastapi-users) | ⭐3.8k |
| `CorrelationID` | `nebula/middleware/correlation_id.py` | [asgi-correlation-id](https://github.com/snok/asgi-correlation-id) | ⭐450 |
| `Token Store` (文件) | `alphaid/auth/token_store.py` | Redis + TTL | - |
| 规则引擎 ×2 | `nebula/ai/fallback_rules.py`+`workflows/` | 抽到单一模块 | - |
| `_SimpleEmbeddingFunction` | `alphaid/core/memory_store.py` | [sentence-transformers](https://github.com/UKPLab/sentence-transformers) | ⭐17k |
| `Orchestrator` 循环 | `alphaid/core/orchestrator.py` | [Celery](https://github.com/celery/celery) / [Temporal](https://github.com/temporalio/sdk-python) | ⭐55k / ⭐12k |
| AgentLoop (部分) | `alphaid/core/agent.py` | [LangGraph](https://github.com/langchain-ai/langgraph) 图结构 | ⭐38k |

### Q2 — 全局单例清单

| 单例 | 文件 | 问题 |
|------|------|------|
| `Container._instance` | `alphaid/container.py` | 测试难隔离 |
| `_event_bus` | `alphaid/core/event_bus.py` | 全局可变状态 |
| `_token_store` | `alphaid/auth/token_store.py` | 文件路径硬编码 |
| `_db` | `nebula/models/session.py` | 连接池生命周期不明确 |
| `settings` | `nebula/config.py` | 模块级副作用 |

### Q3 — 过时模式清单

| 模式 | 文件 | 现代替代 |
|------|------|----------|
| `body: dict` 无 Pydantic | `alphaid/api/agent.py` | `ChatRequest(BaseModel)` |
| `datetime.utcnow()` | `nebula/schemas/auth.py` | `datetime.now(timezone.utc)` |
| `subprocess` 调 alembic | `nebula/models/session.py` | Alembic 原生异步 API |
| `asyncio.get_event_loop()` | `nebula/ai/circuit_breaker.py` | `asyncio.get_running_loop()` |
| `ThreadPoolExecutor` 混用 | `nebula/workflows/engine.py` | 全异步或 `asyncio.to_thread` |
| 手动拼 system prompt | `alphaid/core/agent.py:623-658` | `ChatPromptTemplate` |
| `__TOOL_CALL__` 文本解析 | `alphaid/core/agent.py:593-618` | OpenAI function calling 结构化 |

---

## 📊 模块评分汇总

| 模块 | 文件数 | 评分 | 一句话 |
|------|--------|------|--------|
| **Alpha-ID auth** | 4 | 7/10 | JWT 基础扎实，密钥派生偏弱 |
| **Alpha-ID core/agent** | 2 | 6/10 | 能用但重复代码多、无持久化 |
| **Alpha-ID core/dual_chain** | 1 | 7/10 | 加密合规但无密钥轮换 |
| **Alpha-ID core/memory_store** | 1 | 5/10 | 向量检索语义能力极弱 |
| **Alpha-ID core/twin_brain** | 1 | 6/10 | 状态机设计过度 |
| **Alpha-ID api** | 9 | 5.5/10 | demo 泄露、无持久化 |
| **Alpha-ID entrypoints** | 1 | 4/10 | AIDFairy 名称错误 |
| **Nebula main** | 1 | 6/10 | 中间件顺序有误 |
| **Nebula middleware** | 6 | 6.5/10 | 限流/IP/CorrelationId 需调 |
| **Nebula models** | 4 | 6/10 | 双 Base 问题 |
| **Nebula api** | 9 | 6/10 | 微信模块缺失 |
| **Nebula core** | 6 | 5/10 | 重复造轮子多 |
| **Nebula automation** | 4 | 4.5/10 | 抖音自动化脆弱 |
| **Gateway** | 1 | 7.5/10 | 三层路由清晰，自研合理 |
| **Net-Agent** | 8 | 7/10 | 适配器模式好，crypto dev fallback |
| **Doubao Reader** | 5 | 6/10 | 自研 LevelDB 解析，易损 |
| **Feishu Bot** | 4 | 6/10 | 功能完整但重造轮子 |
| **ghost-capture** | 14 | 6.5/10 | 扩展形态好，CDP 多版本冗余 |
| **Orchestrator** | 1 | 3/10 | PoC 骨架，未集成 |
| **Flow** | 3 | 2/10 | 源码缺失，不可运行 |
| **DS** | 20 | 7.5/10 | MVP 完整，Prisma 需改进 |
| **FAIRY Desktop** | 8 | 7/10 | 方案领先行业 |

---

## 🌐 GitHub 对标项目

### DID / 去中心化身份

| 项目 | Stars | 核心优势 | 借鉴 |
|------|-------|----------|------|
| [spruceid/didkit](https://github.com/spruceid/didkit) | ⭐318 | 跨平台 DID 工具包 | 改为 `did:key` |
| [iotaledger/identity](https://github.com/iotaledger/identity) | ⭐350 | Rust DID Core | W3C 标准对齐 |
| [openwallet-foundation/credo-ts](https://github.com/openwallet-foundation/credo-ts) | ⭐350 | DIDComm v2 + Aries | A2A 通信层 |

### AI Agent 框架

| 项目 | Stars | 核心优势 | 借鉴 |
|------|-------|----------|------|
| [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) | ⭐15k | Handoff + Guardrails | 替代 TwinBrain 编排 |
| [LangGraph](https://github.com/langchain-ai/langgraph) | ⭐38k | StateGraph + Checkpointer | AgentLoop 图结构化 |
| [AutoGen](https://github.com/microsoft/autogen) | ⭐60k | 多 Agent 对话 | A2A 通信协议 |
| [CrewAI](https://github.com/crewAIInc/crewAI) | ⭐56k | 角色化编排 | 多角色 Agent |

### 向量记忆 / RAG

| 项目 | Stars | 核心优势 | 借鉴 |
|------|-------|----------|------|
| [Mem0](https://github.com/mem0ai/mem0) | ⭐61k | 自动记忆提取+去重 | 知链自动提取 |
| [Letta (MemGPT)](https://github.com/letta-ai/letta) | ⭐24k | 三层记忆管理 | 记忆自主管理 |
| [Zep](https://github.com/getzep/zep) | ⭐5k | 知识图谱+时间衰减 | 记忆时效权重 |

### API 网关

| 项目 | Stars | 核心优势 | 借鉴 |
|------|-------|----------|------|
| [Traefik](https://github.com/traefik/traefik) | ⭐64k | 云原生自动发现 | 大规模时切换 |
| [Kong](https://github.com/Kong/kong) | ⭐44k | 插件生态 | 企业功能 |

### 桌面 AI

| 项目 | Stars | 核心优势 |
|------|-------|----------|
| [Miru](https://github.com/kiyotakali/Miru) | ⭐47 | 开源自托管 AI 伴侣 |
| [Live2DPet](https://github.com/x380kkm/Live2DPet) | ⭐71 | Live2D + VOICEVOX |

### 浏览器自动化

| 项目 | Stars | 核心优势 | 借鉴 |
|------|-------|----------|------|
| [Browser-use](https://github.com/browser-use/browser-use) | ⭐107k | Playwright + LLM | 加 DOM 视觉理解 |
| [Playwright](https://github.com/microsoft/playwright) | ⭐76k | 跨浏览器标准 | 服务端兜底 |

---

## 🗑️ 根目录清理建议

### 可立即删除

| 文件/目录 | 原因 |
|-----------|------|
| `_trash/` (42 个脚本) | 明确标记为废弃 |
| `codex-remote/` | 仅含 package.json 的空壳 |
| `skills/baidu-ai-map/` | clawhub 安装，8 天未使用 |
| `docs/` (空) | 从未使用 |
| `logs/` (空) | 日志实际在根目录 |
| `1784806729763.txt` | 不明文件 |
| `41` | 不明文件 |

### 可合并/归档

| 文件 | 建议 |
|------|------|
| `AUDIT_COMPLETE.md`、`GHOST_FULL_AUDIT.md`、`REGISTRY_ALL.md`、`AUDIT_STATUS.md` | 合并为一份主注册表 |
| `fix_*.js` (15 个) | 移入 archive 或删除 |
| `read_db_*.js` (6 个) | 移入 archive 或删除 |
| `GHOST.md` | 更新组件清单和 AgentLoop 状态 |
| `STARTUP.md` + `USER_GUIDE.md` | 明确分工：部署 vs 使用 |

### 需安全处理

| 文件 | 建议 |
|------|------|
| `alipay_private_pkcs1.pem` | 移出仓库，加入 `.gitignore` |
| `alipay_public_key.pem` | 同上 |
| `.env` 文件 | 确认未被 Git 跟踪 |

---

## 📅 改进路线图

### 第 1 周：安全红线

- [ ] 修 registration.py：关闭 demo 返回验证码、不返回私钥、加频率限制
- [ ] 修 jwt.py：改用 HKDF 或强制 32-byte 密钥
- [ ] 修 feishu_webhook.py：改用 hmac.compare_digest
- [ ] 修 rate_limit.py：支持 X-Forwarded-For
- [ ] 移动根目录私钥到安全位置
- [ ] 修 daemon.py：AIDFairy → AidNuro
- [ ] 修 events.py：移除微信模块引用或补全

### 第 2 周：功能接通

- [ ] 统一 SQLAlchemy Base（解决 alembic 漏表）
- [ ] 修中间件顺序（CorrelationId 最外层）
- [ ] 删除重复规则引擎（保留 fallback_rules.py）
- [ ] AgentLoop 加对话历史持久化
- [ ] memory_store.py 启用真实向量嵌入

### 第 3-4 周：架构优化

- [ ] 删除 core/auth.py，统一用 SQLAuthProvider
- [ ] core/metrics.py 换 prometheus-fastapi-instrumentator
- [ ] core/events.py 换 arq
- [ ] 全局单例改为请求级依赖
- [ ] body: dict 全部改为 Pydantic 模型

### 第 1-3 月：长期演进

- [ ] 评估 LangGraph 替代 MasterOrchestrator
- [ ] DID 改为 did:key 方法
- [ ] token_store.py 迁移到 Redis
- [ ] 引入 OpenTelemetry 链路追踪
- [ ] 根目录一次性脚本清理
- [ ] 文档合并统一

---

## ✅ 你做得好的地方（别丢掉了）

1. **Gateway 三层路由** — `/human` `/agent` `/internal` 分离清晰，自研合理
2. **双链记忆隔离** — 私链 AES-GCM、知识链可搜索，隐私分离优于 Mem0
3. **Webhook 安全** — HMAC-SHA256 + timingSafeEqual + fail-closed
4. **Docker 多阶段构建** — DS 的 Dockerfile 用非 root 用户
5. **SSRF 防护** — `_validate_llm_base_url` 显式域名白名单
6. **存储抽象** — StorageBackend ABC 让 SQLite/Postgres 切换容易
7. **alembic 迁移** — Nebula 8 表 + Alpha-ID 5 表都有版本管理
8. **FAIRY 技术选型** — 本地推理 + MCP + 双链记忆，组合领先 Miru/Live2DPet
9. **飞书多后端切换** — AtomCode/ZCode/Codex 可切换
10. **模块边界清晰** — 每个文件职责明确，注释到位

---

## 🎯 最终结论

**你的项目不是一无是处，而是"散落一地的珍珠"。**

核心模块（双链记忆、AgentLoop、Gateway、FAIRY）都有独创设计且领先或对齐行业，但它们被大量重复代码、一次性脚本、重叠文档淹没了。

**三条路选一条：**

1. **做减法** — 砍到只剩一个核心场景（建议：豆包→Gateway→Alpha-ID→Obsidian 这条线），其他全归档
2. **做整理** — 修掉安全问题、统一重复代码、清理根目录，让项目"拿得出手"
3. **做产品** — 基于现有架构做一个真正能让用户用起来的 MVP（Ghost.html 已经有一个不错的壳）

---

> **审计完成。共扫描 392 个 .py、61 个 .md、38 个 .ts、35 个 .js、20 个 .tsx、49 个 .json、14 个 .yaml、12 个 .yml、30 个 .txt、19 个 .bat。派出 21 个 Agent 并行审计。无任何文件被修改。**
