# OpenAPI SDK 生成指南

本项目使用 FastAPI 内置的 OpenAPI 规范生成能力，基于 `custom_openapi()` 函数生成增强版 Schema。

## 生成客户端 SDK

### 1. 获取 OpenAPI Schema

```bash
# 启动服务后访问
curl http://localhost:2002/openapi.json > openapi.json
```

### 2. 使用 openapi-generator 生成客户端

```bash
# TypeScript (用于 flow 前端)
openapi-generator-cli generate \
  -i openapi.json \
  -g typescript-fetch \
  -o ../flow/src/sdk/ \
  --additional-properties=supportsES6=true,npmName=@ghost/sdk

# Python (用于 Agent 插件)
openapi-generator-cli generate \
  -i openapi.json \
  -g python \
  -o ./sdk/python/ \
  --package-name ghost_sdk
```

### 3. 支持的 Generator 语言

| 语言 | Generator | 用途 |
|------|-----------|------|
| TypeScript | `typescript-fetch` | flow 前端 SDK |
| Python | `python` | Agent 插件 / 数据科学 |
| Go | `go` | 高性能 CLI 工具 |
| Java | `spring` | 企业级集成 |

## 认证

所有 SDK 调用需在 Header 中携带 Bearer Token：

```typescript
import { Configuration, DefaultApi } from '@ghost/sdk';

const config = new Configuration({
  accessToken: () => localStorage.getItem('ghost_token') ?? '',
});
const api = new DefaultApi(config);
```

## 版本策略

SDK 版本与 API 版本（`x-api-version: v1`）保持同步。详见 [API_VERSIONING.md](./API_VERSIONING.md)。
