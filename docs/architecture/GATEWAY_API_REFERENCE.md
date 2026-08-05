<!-- ════════════════════════════════════════════════════════════════════ -->
<!-- STATUS: REFERENCE → 详见 GHOST.md v3.0                                -->
<!-- 本文件为 Gateway API 详细参考（端点列表、请求/响应示例、错误码）。      -->
<!-- GHOST.md 第 7 节有端口速查表，本文件保留为 API 开发参考。             -->
<!-- ════════════════════════════════════════════════════════════════════ -->

# Gateway API 参考

> 更新日期：2026-07-27
> 基础 URL：`http://localhost:18080`
> 所有响应统一信封格式，见下文

---

## 响应信封格式

所有 API 返回统一结构：

```json
// 成功（HTTP 200）
{
  "success": true,
  "data": { ... },
  "ts": 1721890000,
  "request_id": "abc123def456"
}

// 失败（HTTP 4xx/5xx）
{
  "success": false,
  "error": "错误描述",
  "ts": 1721890000,
  "request_id": "abc123def456"
}
```

| 字段 | 类型 | 说明 |
|:-----|:-----|:-----|
| `success` | boolean | 请求是否成功 |
| `data` | object | 成功时的业务数据 |
| `error` | string | 失败时的错误描述 |
| `ts` | integer | Unix 时间戳（秒） |
| `request_id` | string | 关联 ID，用于追踪 |

**请求头：**
- `X-Request-ID`：可选，客户端指定关联 ID（12 位十六进制）
- `Authorization`：可选，Bearer Token（代理到后端时透传）

---

## 健康检查

### `GET /health`

公共健康检查，返回各后端服务状态。

**响应示例：**
```json
{
  "success": true,
  "data": {
    "gateway": "ok",
    "alphaid": "ok",
    "obsidian": "ok",
    "netagent": "ok"
  },
  "ts": 1721890000,
  "request_id": "abc123"
}
```

| 字段 | 说明 |
|:-----|:-----|
| `gateway` | 始终 `ok` |
| `alphaid` | `ok` 或 `error` |
| `obsidian` | `ok` 或 `not_found` |
| `netagent` | `ok` 或 `error` |

---

## /v1/human/* — 人类用户接口

### 身份与大脑

#### `GET /v1/human/identity?alpha_id={id}`

获取当前身份。先尝试认证用户资料，失败回退到公开统计。

| 参数 | 类型 | 必填 | 说明 |
|:-----|:-----|:-----|:-----|
| `alpha_id` | string | 否 | Alpha-ID，默认用环境变量 |

**响应 `data`：**
```json
{
  "founder_alpha_id": "Alpha-001",
  "total_users": 1,
  "profile": { ... }
}
```

#### `GET /v1/human/profile`

获取用户资料。

#### `GET /v1/human/brain/status?alpha_id={id}`

获取大脑状态。

#### `POST /v1/human/brain/awake`

唤醒大脑。

**请求体：**
```json
{"alpha_id": "Alpha-001"}
```

---

### 聊天与意图

#### `POST /v1/human/chat`

与 Agent 聊天。限流：10 次/60秒/IP。

**请求体：**
```json
{
  "alpha_id": "Alpha-001",
  "message": "你好，帮我查一下天气"
}
```

**响应 `data`：**
```json
{
  "reply": "今天北京晴，25°C",
  "intent": "weather_query"
}
```

**特殊逻辑：** 如果用户未注册（返回 401），自动注册后重试。

#### `POST /v1/human/intent/parse`

意图解析 — 网关级智能路由。

**请求体：**
```json
{"text": "我是谁"}
```

**响应 `data`：**
```json
{
  "route": "identity",
  "identity": { ... },
  "profile_summary": { ... }
}
```

路由规则：
- 含 "身份/我是谁/did/identity/画像" → 走身份路由
- 其他 → 走聊天路由

---

### 记忆

#### `POST /v1/human/memory/store`

存储记忆到 Alpha-ID。

**请求体：**
```json
{
  "alpha_id": "Alpha-001",
  "content": "今天学到了新东西",
  "category": "general",
  "tags": ["学习", "成长"],
  "sensitivity": 1
}
```

#### `GET /v1/human/memory/graph`

获取记忆知识图谱（d3.js 可视化用）。免费，不调 LLM。

**响应 `data`：**
```json
{
  "nodes": [
    {"id": "abc123", "label": "内容摘要", "category": "chat", "color": "#38bdf8"}
  ],
  "edges": [
    {"from": "abc123", "to": "def456", "label": "标签"}
  ],
  "stats": {
    "memories": 42,
    "connections": 15
  }
}
```

#### `GET /v1/human/memory/search?keyword={kw}&limit={n}`

搜索 Obsidian 知识库。

| 参数 | 类型 | 必填 | 说明 |
|:-----|:-----|:-----|:-----|
| `keyword` | string | 否 | 搜索关键词 |
| `limit` | integer | 否 | 返回数量，默认 20 |

**响应 `data`：**
```json
{
  "results": [
    {
      "title": "笔记标题",
      "file": "note.md",
      "category": "设计",
      "date": "2026-07-20",
      "tags": ["架构", "Gateway"],
      "preview": "内容预览...",
      "modified": 1721890000
    }
  ],
  "total": 1
}
```

---

### 工作流

#### `GET /v1/human/workflows`

获取工作流模板列表（代理到 Nebula）。

#### `POST /v1/human/workflows/execute`

执行工作流。

**请求体：**
```json
{
  "template_id": "travel_planner",
  "params": {"destination": "东京", "days": 5}
}
```

---

### 注册流程

#### `POST /v1/human/register/send-sms`

发送短信验证码。限流：5 次/60秒/IP。

**请求体：**
```json
{"phone": "13800000000"}
```

#### `POST /v1/human/register/verify-sms`

验证短信码。

**请求体：**
```json
{"phone": "13800000000", "code": "123456"}
```

#### `POST /v1/human/register/face-verify`

发起人脸认证。

**请求体：**
```json
{"alpha_id": "Alpha-001", "video_url": "..."}
```

#### `POST /v1/human/register/face-query`

查询人脸认证结果。

**请求体：**
```json
{"session_id": "sess_abc123"}
```

#### `POST /v1/human/register/generate-did`

生成去中心化身份 DID。

**请求体：**
```json
{"alpha_id": "Alpha-001"}
```

**响应 `data`：**
```json
{
  "did": "did:aid:z6Mkpz1x...",
  "public_key": "...",
  "private_key_hint": "存储于本地"
}
```

#### `POST /v1/human/register/complete`

完成注册。

**请求体：**
```json
{
  "alpha_id": "Alpha-001",
  "profile": {"nickname": "用户昵称"}
}
```

---

### 仪表盘

#### `GET /v1/human/dashboard`

统一仪表盘 — 单次调用返回所有需要的数据（并行请求后端）。

**响应 `data`：**
```json
{
  "identity": {
    "alpha_id": "Alpha-001",
    "total_users": 1,
    "state": "ready"
  },
  "profile": { ... }
}
```

---

## /v1/agent/* — Agent 生态接口

#### `GET /v1/agent/interact/topology`

获取 Agent 网络拓扑。

**响应 `data`：**
```json
{
  "nodes": [{"id": "agent_1", "type": "private"}],
  "edges": [{"from": "agent_1", "to": "agent_2"}]
}
```

#### `GET /v1/agent/feeds/latest?industry={ind}&limit={n}`

获取行业资讯。

| 参数 | 类型 | 必填 | 说明 |
|:-----|:-----|:-----|:-----|
| `industry` | string | 否 | 行业筛选（跨境电商/短视频/...） |
| `limit` | integer | 否 | 返回数量，默认 20 |

**响应 `data`：**
```json
{
  "results": [
    {
      "title": "2026跨境电商趋势",
      "category": "跨境电商",
      "preview": "内容预览...",
      "updated_at": 1721890000,
      "content": "完整内容..."
    }
  ],
  "total": 1
}
```

#### `POST /v1/agent/feeds/subscribe`

订阅行业资讯更新。

**请求体：**
```json
{"industry": "跨境电商"}
```

**响应 `data`：**
```json
{"status": "subscribed", "industry": "跨境电商"}
```

---

## /v1/internal/* — 内部运营接口

> ⚠️ 这些接口仅限平台内部使用，部分有 IP 白名单限制。

#### `POST /v1/internal/orchestrator/task/submit`

提交任务到编排器。

**请求体：**
```json
{
  "task_type": "data_collection",
  "params": {"source": "chatgpt"}
}
```

#### `GET /v1/internal/orchestrator/tasks`

获取所有编排器任务。

#### `GET /v1/internal/orchestrator/task/{task_id}`

获取指定任务状态。

**响应 `data`：**
```json
{
  "task_id": "task_123",
  "status": "running",
  "progress": 0.6,
  "result": null
}
```

#### `GET /v1/internal/obsidian/status`

检查 Obsidian vault 状态。

**响应 `data`：**
```json
{
  "exists": true,
  "path": "D:\\Obsidian\\Ghost知识库",
  "file_count": 42,
  "recent_file": "2026-07-27.md"
}
```

---

## /v1/net/* — 网络操作接口

#### `ALL /v1/net/{path}`

代理到 Net-Agent 服务器（路由器管理）。支持 GET/POST/PUT/DELETE。

**透传规则：**
- `Authorization` 头原样透传
- Net-Agent 自行处理权限校验

**示例：**
```bash
# 获取路由器状态
GET /v1/net/router/status

# 重启路由器
POST /v1/net/router/reboot
```

---

## 错误码

| HTTP 码 | 含义 | 场景 |
|:--------|:-----|:-----|
| 200 | 成功 | 正常返回 |
| 400 | 请求参数错误 | 缺少必填字段 |
| 403 | 禁止访问 | 非本地请求访问内部接口 |
| 429 | 请求过于频繁 | 触发限流 |
| 500 | 服务器内部错误 | 未捕获异常 |
| 502 | 后端错误 | 后端返回错误或不可达 |

**502 响应示例：**
```json
{
  "success": false,
  "error": "backend returned 404",
  "data": {"_error": "backend returned 404", "_raw": "..."},
  "ts": 1721890000,
  "request_id": "abc123"
}
```
