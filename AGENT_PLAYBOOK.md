# Agent 工作手册 — MW / Ghost 项目

> **先读 [`PROJECT_BRAIN.md`](./PROJECT_BRAIN.md) 了解项目全貌，再读此文档。**
> 最后更新：2026-07-24

---

## 1. 快速参考

| 目录 | 职责 | 端口 | 状态 | 能否改动 |
|------|------|------|------|----------|
| `Ghost.html` | **唯一官网** | — | ✅ 已部署 | ✅ 谨慎修改 |
| `ghost-main/gateway/` | **Ghost API Gateway** | **18080** | ✅ 运行中 | ✅ 网关路由 |
| `alphaid/` | 身份层（DID/JWT/记忆） | 8000 | ✅ 运行中 | ✅ |
| `DS/` | 电商后端 API | 3004 | ✅ 运行中 | ✅ |
| `core/` | 编排层 | 3001 | ❓ | ✅ |
| `nebula/` | 执行层 | 2002 | ❌ 未运行 | ✅ 代码完整 |
| `flow/` | Next.js 功能原型 | 3000/3001 | ❌ 未部署 | ⚠️ 别往里加官网功能 |
| `obsidian-plugin/` | Obsidian 插件 | — | — | ✅ |

---

## 2. 铁律（违反任何一条都是错的）

### 2.1 官网只改 Ghost.html
- **永远不要**往 `flow/apps/web/` 里加"官网功能"
- **永远不要**让用户去看 `localhost:3000` 或其他端口
- 用户问"官网在哪" → 回答 `Ghost.html`，没有第二个答案

### 2.2 所有 API 请求走 Ghost Gateway (18080)
- **永远不要**在 Ghost.html 里直接调 `localhost:8000` 或 `localhost:3004`
- 统一入口：`http://localhost:18080`
- Ghost.html 里有常量 `GATEWAY_API = 'http://localhost:18080'`

### 2.3 电商数据走 DS API（通过网关）
- 网关路径：`/v1/shop`、`/v1/products`、`/v1/orders`、`/v1/ecommerce/*`
- DS 后端连接 Shoplazza（店匠）`nero.myshoplaza.com`
- 不要在 Ghost.html 里直接调 Shoplazza API（跨域+暴露 token）

### 2.4 身份数据走 alphaid（通过网关）
- 网关路径：`/v1/identity`、`/v1/brain/*`、`/v1/network/*`、`/v1/chat`、`/v1/profile`
- alphaid 是唯一身份源，不要在 nebula 或 flow/api 里新建身份模块

### 2.5 改之前先确认范围
- 用户说"加到官网" → 改 Ghost.html
- 用户说"加到网关" → 改 `ghost-main/gateway/app.py`
- 用户说"加到电商" → 改 DS/ 或网关路由
- 用户说"加到身份层" → 改 alphaid/
- **不确定就问，不要猜**

### 2.6 不要创建重复功能
- 如果 Ghost.html 已经有电商面板，不要在 flow/web 里再做一套
- 如果 alphaid 已经有 DID 生成，不要在 core/ 或 nebula/ 里再造一套
- 动手前先 grep 检查是否已有类似实现

---

## 3. Ghost Gateway API 参考

> **前端只认这个入口，不要绕开网关直连后端。**

| 网关端点 | 代理到 | 功能 |
|----------|--------|------|
| `GET /health` | — | 网关自身健康 |
| `GET /v1/dashboard` | alphaid+DS 聚合 | **全量数据一次性返回** |
| `GET /v1/identity` | alphaid :8000 | 身份信息 |
| `GET /v1/profile` | alphaid :8000 | 用户画像 |
| `GET /v1/brain/status` | alphaid :8000 | Brain 状态 |
| `POST /v1/brain/awake` | alphaid :8000 | 唤醒 Brain |
| `GET /v1/network/topology` | alphaid :8000 | A2A 网络拓扑 |
| `POST /v1/chat` | alphaid :8000 | AI 对话 |
| `POST /v1/intent/parse` | 智能路由 | 按关键词分发 |
| `GET /v1/shop` | DS :3004 | 店铺信息 |
| `GET /v1/products` | DS :3004 | 商品列表 |
| `GET /v1/orders` | DS :3004 | 订单列表 |
| `GET /v1/ecommerce/stats` | DS :3004 | 电商统计 |
| `POST /v1/ecommerce/sync` | DS :3004 | 触发同步 |
| `GET /v1/workflows` | nebula :2002 | 工作流列表（待连） |
| `POST /v1/workflows/execute` | nebula :2002 | 执行工作流（待连） |

**Intent 路由规则：**
- "订单/商品/店铺" → DS 电商
- "身份/DID/记忆" → alphaid 身份
- 其他 → alphaid chat

---

## 4. 后端 API 参考（供网关路由参考，前端不要直接调）

### 4.1 alphaid (port 8000)

| API | 方法 | 功能 |
|-----|------|------|
| `/identity` | GET | 身份信息（需 X-Alpha-ID header） |
| `/brain/status` | GET | Brain 状态（参数：alpha_id） |
| `/brain/awake` | POST | 唤醒 Brain |
| `/network/topology` | GET | 网络拓扑 |
| `/api/profile` | GET | 用户画像 |
| `/chat` | POST | AI 对话 |
| `/health` | GET | 健康检查 |

### 4.2 DS (port 3004)

| API | 方法 | 功能 |
|-----|------|------|
| `/api/shop` | GET | 店铺信息 |
| `/api/products` | GET | 商品列表 |
| `/api/orders` | GET | 订单列表 |
| `/api/orders/[id]/fulfill` | POST | 订单发货 |
| `/api/stats` | GET | 统计数据 |
| `/api/sync` | POST | 手动同步 |
| `/api/webhook/shoplazza` | POST/GET | 事件回调 |
| `/api/health` | GET | 健康检查 |

**店铺**：`nero.myshoplaza.com`

---

## 5. 常见错误（已发生过，不要再犯）

| 错误 | 后果 | 正确做法 |
|------|------|----------|
| Ghost.html 直连 alphaid:8000 | 绕开网关，架构混乱 | 走 Gateway :18080 |
| Ghost.html 直连 DS:3004 | 绕开网关，架构混乱 | 走 Gateway :18080 |
| 往 flow/web 加功能 | 用户看不到 | 只改 Ghost.html |
| 让用户看 localhost:3000 | 那不是官网 | 只说 Ghost.html |
| 直接调 Shoplazza API | 跨域 + token 泄露 | 走网关 → DS |
| nebula 里新建身份模块 | 与 alphaid 重复 | 调 alphaid API |
| 创建重复功能 | 代码混乱 | 先 grep 检查 |
| 不读文档就动手 | 不了解架构 | 先读 PROJECT_BRAIN.md |

---

## 6. 改代码前的 Checklist

- [ ] 我要改的东西属于哪一层？（官网 / 网关 / DS / alphaid / core / nebula / flow）
- [ ] 是否已有类似功能？（grep 检查）
- [ ] 改动会影响其他层吗？
- [ ] 前端请求是否走了网关？（不要直连后端）
- [ ] 测试覆盖了吗？

---

## 7. 新会话启动流程

```
1. 读 PROJECT_BRAIN.md     → 了解全貌
2. 读 AGENT_PLAYBOOK.md    → 了解规范（此文档）
3. 理解当前任务           → 属于哪一层？哪个 Phase？
4. 检查已有代码           → grep 搜索，避免重复
5. 确认方案               → 不确定就问用户
6. 动手实现               → 遵循架构红线
7. 验证                   → 运行测试，检查前端
8. 提交                   → git commit，写清楚改了什么
```
