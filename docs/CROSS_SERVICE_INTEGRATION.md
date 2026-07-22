# 跨服务数据流 — mindflow-map ↔ DS

## 概述

mindflow-map 和 DS 通过 HTTP API 进行服务间通信，使用 API Key 认证。

```
┌─────────────────────────┐         ┌─────────────────────────┐
│    mindflow-map (:2002) │         │       DS (:3004)        │
│                         │         │                         │
│  /api/v1/ds/metrics  ───┼────────►│  /api/dashboard/metrics │
│  /api/v1/ds/alerts   ───┼────────►│  /api/dashboard/alerts  │
│  /api/v1/ds/products ───┼────────►│  /api/shopify/products  │
│  /api/v1/ds/orders   ───┼────────►│  /api/shopify/orders    │
│  /api/v1/ds/health   ───┼────────►│  /api/health            │
│                         │         │                         │
│                         │◄────────┤  /api/webhooks/mindflow │
│                         │  POST   │       -map              │
└─────────────────────────┘         └─────────────────────────┘
```

## 认证方式

### mindflow-map → DS
- 请求头：`X-Service-Key: {DS_API_KEY}`
- DS 端通过 `validateServiceKey()` 中间件验证

### DS → mindflow-map
- 请求头：`Authorization: Bearer {token}` 或 `X-API-Key: {key}`
- mindflow-map 端通过 `AuthMiddleware` 验证

## 端点详情

### mindflow-map 代理端点（新增）

| 端点 | 方法 | 目标 | 说明 |
|------|------|------|------|
| `/api/v1/ds/metrics` | GET | DS `/api/dashboard/metrics` | Dashboard 指标 |
| `/api/v1/ds/alerts` | GET | DS `/api/dashboard/alerts` | 告警列表 |
| `/api/v1/ds/products` | GET | DS `/api/shopify/products` | Shopify 产品 |
| `/api/v1/ds/orders` | GET | DS `/api/shopify/orders` | Shopify 订单 |
| `/api/v1/ds/health` | GET | DS `/api/health` | 健康检查 |

### DS Webhook 端点（新增）

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/webhooks/mindflow-map` | POST | 接收 mindflow-map 事件 |
| `/api/webhooks/mindflow-map` | GET | 健康检查 |

### 支持的事件类型

| 事件 | 说明 | DS 处理 |
|------|------|---------|
| `approval.completed` | 审批通过 | 创建 info 告警 |
| `approval.rejected` | 审批拒绝 | 创建 high 告警 |
| `precheck.completed` | 内容预审完成 | 创建 warning/info 告警 |
| `workflow.completed` | 工作流完成 | 仅记录日志 |

## 配置

### mindflow-map `.env`
```bash
DS_API_URL=http://localhost:3004
DS_API_KEY=your_shared_secret_key
```

### DS `.env`
```bash
DS_API_KEY=your_shared_secret_key
MINDFLOW_MAP_URL=http://localhost:2002
```

## 错误处理

- **DS 不可用**：mindflow-map 返回 502 + 错误详情
- **认证失败**：DS 返回 401
- **超时**：默认 10 秒，可配置
- **网络错误**：记录日志，不阻塞主流程

## 测试

```bash
# 测试 DS 客户端
cd mindflow-map && pytest tests/unit/test_ds_client.py -v

# 测试 Service Auth
cd DS && npx vitest run src/lib/middleware/service-auth.test.ts
```
