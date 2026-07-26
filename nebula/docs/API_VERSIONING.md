# API 版本控制策略

## 当前版本

- **v1** — 当前稳定版本（`/api/v1/`）

## 版本规则

### URL 前缀

所有业务 API 必须携带版本前缀：

```
/api/v1/brain/memory
/api/v1/chat/stream
/api/v1/intent/parse
```

### 版本兼容性

| 规则 | 说明 |
|------|------|
| 向后兼容 | v1.x 的变更必须向后兼容 |
| 破坏性变更 | 必须升级到 v2，保留 v1 至少 6 个月 |
| 弃用通知 | 通过 `Deprecation` Response Header 提前通知 |

### v1 → v2 迁移路径

当需要破坏性变更时：

1. 引入 `/api/v2/` 端点
2. v1 端点返回 `301 Moved Permanently` + `Location` Header 指向 v2
3. 维护双版本至少 6 个月
4. 6 个月后 v1 返回 `410 Gone`

### OpenAPI Schema 标记

Schema 中通过 `x-api-version` 字段标识当前版本：

```json
{
  "info": {
    "x-api-version": "v1"
  }
}
```

### 客户端版本协商

客户端在 `Accept` 头中声明版本偏好：

```
Accept: application/vnd.ghost.v1+json
```

服务端按优先级响应：
1. 客户端指定版本
2. 最新版本（v1）
