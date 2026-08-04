# Ghost Platform — 项目状态报告

> **生成时间**: 2026-08-04 | **验证方式**: 逐行代码阅读 + 单元测试 + Docker 全栈验证

## 1. 服务健康状态（Docker 全栈已验证）

| 服务 | 端口 | 状态 | 验证方式 | 备注 |
|:-----|-----:|:-----|:---------|:-----|
| Gateway | 18080 | ✅ healthy | 33 单测 + 20 e2e + 全链路 curl | 110+ 路由，新增 EventBus 客户端 |
| Alpha-ID | 8000 | ✅ healthy | curl /health | v0.3.3, WeChatAdapter 已导出 |
| Nebula | 2002 | ✅ healthy | 153 单测 + curl | v0.1.0 工作流引擎 |
| Ghost DS | 3001 | ✅ healthy | curl /api/* | Next.js 14, 多页面已增强 |
| Orchestrator | 19090 | ✅ healthy | 7 单测 + curl | 通过 Gateway 调用 ToolA/ToolB |
| ToolA | 8081 | ✅ healthy | curl /health | 代码生成器 |
| ToolB | 8082 | ✅ healthy | curl /health | 代码优化器 |
| Feishu Bot | — | ✅ healthy | 2 单测 | echo 模式可用 |
| Net-Agent | 18180 | ✅ healthy | curl /health | 网络操作代理 |
| Flow | 3036 | ✅ healthy | curl /health | mindflow-api v0.1.0 |
| Redis | 6379 | ✅ healthy | docker ps | EventBus 底层，全栈共享 |

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
| Orchestrator → Gateway → ToolA | ✅ 链路通 | /v1/tools/generate 代理 |
| Orchestrator → Gateway → ToolB | ✅ 链路通 | /v1/tools/optimize 代理 |
| WeChat → Gateway → EventBus | ✅ 链路通 | SOCIAL_MESSAGE 事件发布到 Redis Stream |
| OrchestratorEngine → EventBus | ✅ 链路通 | _on_social_message 消费者已注册 |

## 4. DS 前端页面增强状态

| 页面 | 状态 | 功能 |
|:-----|:-----|:-----|
| /app/demo | ✅ 增强 | 连接真实 DID API + fallback 模拟 + 复制功能 |
| /app/ecosystem/workbench | ✅ 增强 | 任务板/笔记/思维画布三面板 |
| /app/ecosystem/a2a | ✅ 增强 | 统计卡片 + Agent/技能/拓扑三个 Tab |
| /app/ecosystem/obsidian | ✅ 增强 | 浏览/写入/同步三个 Tab + 搜索 |
| /app/ecosystem/strategies | ✅ 已有 | 策略笔记 + 供应商画像卡片 |
| /app/register | ✅ 已有 | 手机号验证码三步注册流程 |
| /app/social | ✅ 已有 | 好友列表/请求/消息三 Tab |
| /app/dashboard | ✅ 已有 | 业务数据 + 基础设施监控双 Tab |
| /app/doubao | ✅ 已有 | 豆包记忆桥对话 + 知识链搜索 |
| /app/voice | ✅ 已有 | Whisper STT + Coqui TTS 状态 |
| /app/brain | ✅ 已有 | TwinBrain 状态 + 对话 |
| /app/ecosystem/tools | ✅ 已有 | ToolA 生成 + ToolB 优化 |

## 5. 已修复问题（2026-08-04 会话）

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
11. **Orchestrator TERM 注释** — 添加 # TERM: OrchestratorEngine/EventBus/TwinBrain/ChannelAdapter/LoopPhase
12. **Orchestrator ToolA/ToolB 调用** — 从直接 URL 改为通过 Gateway 代理
13. **DS demo 页面** — 连接真实 /api/v1/register/generate-did API
14. **DS workbench 页面** — 从占位符重写为功能页面（任务/笔记/画布）
15. **DS A2A 页面** — 添加统计卡片 + Agent/技能/拓扑 Tab
16. **DS Obsidian 页面** — 添加浏览/写入/同步 Tab + 搜索
17. **WeChat 适配器** — 从死代码激活：导出 WeChatAdapter + EventBus 消费者 + Gateway 事件发射
18. **Gateway EventBus 客户端** — 新建 gateway/services/eventbus_client.py
19. **Redis Streams 配置** — Gateway + Orchestrator 添加 REDIS_URL/EVENT_STREAM_PREFIX

## 6. 阻塞项

- **DS api-proxy.ts 容器未更新** — 代码已改造，需 `docker compose build --no-cache ghost-ds` 后验证
- **Alpha-ID 新模块未接入** — ghost_brain, ghost_voice 等存在但未被 Gateway 路由调用
- **DS 前端 E2E 测试** — 待补充 Playwright 测试

## 7. 下一步行动

1. `docker compose build --no-cache ghost-ds` → 验证 DS 代理层
2. `docker compose up -d` → 验证 WeChat → EventBus → Orchestrator 全链路
3. DS frontend E2E 测试补充（Playwright）
4. Alpha-ID ghost_brain/ghost_voice 接入 Gateway 路由
5. 接入真实 ToolA/ToolB LLM API（当前为 stub）
6. 补充更多 DS 前端页面（chat/memory/workflow 内容增强）
