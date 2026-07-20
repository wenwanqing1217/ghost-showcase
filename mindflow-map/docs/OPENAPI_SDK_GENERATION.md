# OpenAPI SDK 生成指南

本文档说明如何基于 MindFlow Map 的 OpenAPI Schema 生成客户端 SDK。

## 1. 导出 OpenAPI Schema

```bash
# 启动服务
uvicorn mindflow_map.main:app --host 0.0.0.0 --port 8000

# 导出 Schema
curl -s http://localhost:8000/openapi.json -o openapi.json
```

或使用提供的脚本：

```bash
python scripts/generate_openapi_spec.py
```

## 2. 生成 TypeScript 客户端

需要安装 [OpenAPI Generator](https://openapi-generator.tech/)：

```bash
# 安装 OpenAPI Generator CLI（需要 Java）
# 或使用 Docker：
docker run --rm -v ${PWD}:/local openapitools/openapi-generator-cli generate \
  -i /local/openapi.json \
  -g typescript-fetch \
  -o /local/sdk/typescript \
  --additional-properties=typescriptThreePlus=true,npmName=mindflow-map-client
```

## 3. 生成 Python 客户端

```bash
docker run --rm -v ${PWD}:/local openapitools/openapi-generator-cli generate \
  -i /local/openapi.json \
  -g python \
  -o /local/sdk/python \
  --additional-properties=packageName=mindflow_map_client
```

## 4. 生成 Go 客户端

```bash
docker run --rm -v ${PWD}:/local openapitools/openapi-generator-cli generate \
  -i /local/openapi.json \
  -g go \
  -o /local/sdk/go \
  --additional-properties=packageName=mindflowmap
```

## 5. 验证 Schema

```bash
# 使用 openapi-cli 验证
npx @redocly/openapi-cli@latest lint openapi.json

# 或使用 Docker
docker run --rm -v ${PWD}:/local redocly/openapi-cli lint /local/openapi.json
```
