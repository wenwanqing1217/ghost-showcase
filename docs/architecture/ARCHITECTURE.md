# Ghost 统一技术架构文档

> 更新日期：2026-07-27
> 合并自：ARCHITECTURE_DESIGN.md + ARCHITEATE_REDESIGN.md + GLOBAL_MINDMAP.md
> 状态：反映当前代码实际状态（已修复问题标注 ✅）

---

## 一、工程整体结构

统一单主工程 `ghost-main/`，业务模块依附底层架构，底层稳定不动，上层业务可独立迭代。

```
ghost-main/
├── gateway/              ← 统一 API 网关（:18080）
├── alphaid/projects/     ← Alpha-ID 核心服务（:8000）
├── nebula/               ← 工作流引擎（:2002）
├── flow/apps/api/        ← AI 路由 + Computer Use（:3001）
├── net-agent/            ← 路由器管理（:18180）
├── orchestrator/         ← 任务调度（:19090）
├── doubao_reader/        ← 豆包桌面日志扫描器
└── docs/                 ← 本文档所在
```

---

## 二、Gateway 网关（统一入口）

### 2.1 定位

Gateway 是所有外部请求的统一入口，代理到各后端服务。四层路由：

| 路由前缀 | 用途 | 目标后端 |
|:--------|:-----|:--------|
| `/v1/human/*` | 人类用户接口 | Alpha-ID |
| `/v1/agent/*` | Agent 生态接口 |
| `/v1/internal/*` | 内部运营接口 |
| `/v1/net/*` | 网络操作接口 | Net-Agent |

### 2.2 模块结构（2026-07-27 重构完成）

```
gateway/
├── app.py              ← 入口：lifespan + 中间件 + 路由挂载 + 扫描器
├── config.py           ← 集中配置（URL/端口/CORS/限流）
├── middleware/
│   ├── correlation.py  ← 请求 ID 注入 + 访问日志
│   └── rate_limit.py   ← 滑动窗口限流
├── services/
│   ├── proxy.py        ← HTTP 代理 + 响应封装（ok/fail）
│   ├── obsidian.py     ← Obsidian 读写/搜索/订阅
│   └── memory_graph.py ← SQLite → d3.js 知识图谱
├── routes/
│   ├── human.py        ← /v1/human/*（身份/聊天/记忆/注册/仪表盘）
│   ├── agent.py        ← /v1/agent/*（拓扑/订阅）
│   ├── internal.py     ← /v1/internal/*（豆包/编排/Obsidian）
│   └── net.py          ← /v1/net/*（Net-Agent 代理）
└── tests/
    ├── conftest.py     ← 测试 fixtures + mock
    ├── test_health.py  ← 6 个健康检查测试
    └── test_rate_limit.py ← 7 个限流/代理测试
```

### 2.3 设计原则

1. **零信任默认**：CORS 显式白名单，生产环境通配符被拦截
2. **可观测**：结构化日志 + correlation ID + 请求耗时
3. **弹性**：超时控制、健康检查、优雅降级
4. **角色无关**：用户可同时是 consumer/creator/developer

### 2.4 HTTP Client 生命周期

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    client = httpx.AsyncClient(
        timeout=30.0,
        limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
    )
    yield
    await client.aclose()
```

- 连接池：最大 100 连接，20 个 keepalive
- 超时：30 秒
- 单一真源：`services.proxy.client`，lifespan 和路由共享同一绑定

### 2.5 响应信封格式

所有 API 统一返回：

```json
// 成功
{"success": true, "data": {...}, "ts": 1721890000, "request_id": "abc123"}

// 失败
{"success": false, "error": "...", "ts": 1721890000, "request_id": "abc123"}
```

- `ts`：Unix 时间戳（秒）
- `request_id`：关联 ID，从 `X-Request-ID` 头传入或自动生成

### 2.6 限流策略

| 端点 | 限制 | 窗口 |
|:-----|:-----|:-----|
| 默认 | 5 次 | 60 秒 |
| `/v1/human/chat` | 10 次 | 60 秒 |
| `/v1/human/register/send-sms` | 5 次 | 60 秒 |

算法：滑动窗口，键 = `功能:客户端IP`

### 2.7 Doubao 扫描器

后台守护线程，每 2 分钟扫描一次豆包桌面 App LevelDB：
1. 读取所有会话（最多处理 5 个）
2. POST 到 `/v1/internal/doubao/capture` 存储
3. 触发 Obsidian 整理 + 批量关联

---

## 三、服务依赖地图

### 3.1 服务清单

| 服务 | 端口 | 职责 | 状态 |
|:-----|:-----|:-----|:-----|
| Alpha-ID | 8000 | 身份/记忆/注册/聊天 | ✅ 运行中 |
| Gateway | 18080 | 统一入口 + 代理 | ✅ 运行中 |
| Nebula | 2002 | 工作流引擎 | ✅ 运行中 |
| Flow/API | 3001 | AI 路由 + Computer Use | ⚠️ 可选 |
| Net-Agent | 18180 | 路由器管理 | ⚠️ 可选 |
| Orchestrator | 19090 | 任务调度 | ⚠️ 可选 |

### 3.2 调用关系

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  浏览器/前端  │────→│   Gateway   │────→│  Alpha-ID   │
│  Ghost.html  │     │   :18080    │     │   :8000     │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
          ┌────────────────┼────────────────┐
          ↓                ↓                ↓
    ┌──────────┐    ┌──────────┐    ┌──────────┐
    │  Nebula  │    │ Net-Agent│    │Orchestrat│
    │  :2002   │    │  :18180  │    │  :19090  │
    └──────────┘    └──────────┘    └──────────┘

┌─────────────┐     ┌─────────────┐
│ Doubao 扫描器│────→│  Gateway    │  (自调用 /v1/internal/doubao/capture)
│ (后台线程)   │     │  :18080     │
└─────────────┘     └─────────────┘
```

### 3.3 数据流

**用户请求流程：**
1. 前端 → Gateway（带 X-Request-ID 可选）
2. Gateway → 路由匹配 → 代理到后端
3. 后端响应 → 信封封装 → 返回前端

**豆包采集流程：**
1. 扫描器读 LevelDB → 提取会话
2. POST → Gateway → `/v1/internal/doubao/capture`
3. 存储到 Alpha-ID `/memory/store`
4. 写入 Obsidian vault
5. 触发整理 + 关联

---

## 四、Alpha-ID 核心服务

### 4.1 已完成模块 ✅

| 模块 | 行数 | 说明 |
|:-----|:-----|:-----|
| DID 身份系统 | - | W3C 标准，Ed25519 密钥对 |
| 双链记忆 | - | 私链（本地加密）+ 知链（业务知识） |
| 注册流程 | - | SMS + 支付宝人脸 + DID 生成 |
| 风控引擎 | - | 五层 Token/积分防护 |
| AgentLoop | 813 | Agent 执行循环 |
| TwinBrain | 690 | 双脑状态管理 |
| A2A 协议 | 410 | 跨智能体通信 |
| 可观测性 | 553 | 指标 + 日志 |
| 故障恢复 | 534 | 自动恢复机制 |
| 采集器 | 1,487 | ChatGPT/Trae 数据导入 |

### 4.2 待接通模块

| 模块 | 状态 | 接通方式 |
|:-----|:-----|:--------|
| AgentLoop → API | 已写未接 | 路由调用 `AgentLoop.run()` |
| TwinBrain → AgentLoop | 已写未接 | 初始化注入 |
| A2A → Gateway | 已写未接 | Gateway 新增 `/v1/a2a/*` |
| 可观测性 → 中间件 | 已写未接 | FastAPI 中间件注册 |

---

## 五、前端架构（Ghost.html）

### 5.1 三视图结构

```
Ghost 官网 (homepageView)
  └─ Landing / 功能介绍 / 演示 / 注册入口

A2A 生态区 (ecosystemView)
  ├─ 控制台：四层 Agent 状态总览
  ├─ 我的 Agent：个人 Agent 集群管理
  ├─ A2A 网络：协作拓扑 + 通信日志
  ├─ 记忆图谱：双链记忆可视化
  ├─ 对话记录：与 Agent 的对话历史
  └─ 设置：身份/偏好

Mindflow 人机协作 (mindflowView)
  ├─ 画布：思维导图 + Agent 协作
  ├─ 任务看板：待办/进行中/已完成
  ├─ 笔记库：知识卡片
  ├─ 人格画像：AI 对用户的认知模型
  └─ 项目时间线：Agent 执行历史
```

### 5.2 文件拆分计划

| 状态 | 说明 |
|:-----|:-----|
| 计划中 | ghost.html → 保留 HTML 结构 |
| 计划中 | ghost.css → 提取所有 `<style>` |
| 计划中 | ghost.js → 提取所有 `<script>` |

---

## 六、已修复安全问题 ✅

| 编号 | 问题 | 修复方式 |
|:-----|:-----|:--------|
| S-01 | 百度地图 Token 硬编码 | 改为 `os.getenv()` |
| S-02 | PostgreSQL 默认密码 | 改为 `${POSTGRES_PASSWORD:?error}` |
| S-03 | PyPI 入口指向已删模块 | 删 `aid-daemon`，修 `aid-api` |
| S-04 | PyPI 入口指向已删模块 | 同上 |
| +13 项 | JWT/A2A/SMS/CSRF 等 | 全部修复（详见 audit 文档） |

---

## 七、开发执行顺序

```
Phase 1（已完成）：安全修复 + Gateway 重构
  ✅ 13 项安全修复
  ✅ Gateway 876 行 → 13 模块拆分
  ✅ 13 个测试通过

Phase 2（进行中）：核心功能接通
  🔄 AgentLoop → API 路由
  🔄 TwinBrain → AgentLoop
  🔄 可观测性 → FastAPI 中间件

Phase 3（待开始）：前端重构
  ⏳ Ghost.html 拆 3 文件
  ⏳ A2A 生态区 UI
  ⏳ Mindflow 人机协作

Phase 4（持续）：内容填充
  ⏳ 行业资讯采集上量
  ⏳ 飞书/豆包入口稳定
  ⏳ 商业生态 UI
```

---

## 八、名词表

| 术语 | 定义 |
|:-----|:-----|
| Alpha-ID | 用户终身唯一实名 DID，人脸+身份证核验生成 |
| FID | 第三方服务商/企业身份，用于上架技能、收益结算 |
| 双链记忆 | 私链（本地隐私加密）+ 知链（公开业务知识） |
| A2A | Agent-to-Agent 跨主体可信通信协议 |
| MCP | Model Context Protocol，工具调用适配标准 |
| 双层网关 | 私有网关（个人隐私）+ 公共网关（外网通信） |
| 星点积分 | 平台合规计费介质，1:1 锚定人民币 |
| 联邦学习 | Agent 技能互通且不泄露原始隐私数据 |
| Doubao | 豆包桌面 App，扫描其 LevelDB 获取对话 |
| Obsidian | 本地 Markdown 知识库，双向同步 |
