# API 版本控制策略

## 当前版本

当前所有业务 API 均以 `/api/v1/` 为前缀，属于 **v1** 版本。

| 路径 | 版本 |
|------|------|
| `/api/v1/map` | v1 |
| `/api/v1/workflow` | v1 |
| `/api/v1/wechat` | v1 |
| `/api/v1/automation` | v1 |
| `/api/v1/shortdramas` | v1 |
| `/api/v1/autopilot` | v1 |
| `/api/v1/streaming` | v1 |
| `/api/v1/approvals` | v1 |
| `/api/v1/events` | v1 |

非版本化路径：
- `/health/*` — 健康检查，无版本限制
- `/docs`、`/redoc`、`/openapi.json` — 文档与元数据
- `/static/*`、`/editor/*` — 静态资源
- `/`、`/workspace` — 前端页面

## 版本标识

OpenAPI Schema 的 `info.x-api-version` 字段标识当前文档对应的 API 版本。

## 向后兼容承诺

- v1 版本接口在 **至少 6 个月内**保持兼容。
- 废弃接口将在响应头 `Sunset` 和 OpenAPI `deprecated` 标记中提前告知。
- 重大变更将发布新的版本路径（如 `/api/v2/`），v1 并行保留。

## 引入 v2 的触发条件

- 请求/响应模型发生不兼容变更
- 认证机制升级（如 OAuth2、mTLS）
- 分页、过滤、排序语义变更
- 性能优化导致行为差异

## 客户端适配

- 新客户端应始终从 `/openapi.json` 读取最新 Schema。
- 生产环境 SDK 由 `openapi-generator` 根据当前版本 Schema 生成，见 [OPENAPI_SDK_GENERATION.md](./OPENAPI_SDK_GENERATION.md)。
