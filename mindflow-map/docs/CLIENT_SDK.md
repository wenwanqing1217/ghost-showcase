# Client SDK 使用指南

本文档说明如何获取和使用 MindFlow Map 的客户端 SDK。

## 1. TypeScript SDK

### 安装

```bash
npm install mindflow-map-client
# 或
yarn add mindflow-map-client
# 或
pnpm add mindflow-map-client
```

### 使用示例

```typescript
import { MindFlowMapClient } from 'mindflow-map-client';

const client = new MindFlowMapClient({
  baseUrl: 'https://api.mindflow.ai',
  apiKey: 'your-api-key',
});

// 搜索地点
const searchResult = await client.map.search({
  query: '中关村',
  city: '北京',
});

// 规划路线
const route = await client.map.route({
  origin: '天安门',
  destination: '中关村',
  mode: 'driving',
});

// 执行工作流
const workflow = await client.workflow.execute({
  text: '帮我规划去故宫的路线',
  user_id: 'user-001',
});
```

## 2. Python SDK

### 安装

```bash
pip install mindflow-map-client
```

### 使用示例

```python
from mindflow_map_client import MindFlowMapClient

client = MindFlowMapClient(
    base_url="https://api.mindflow.ai",
    api_key="your-api-key",
)

# 搜索地点
result = client.map.search(query="中关村", city="北京")

# 规划路线
route = client.map.route(
    origin="天安门",
    destination="中关村",
    mode="driving",
)

# 执行工作流
workflow = client.workflow.execute(text="帮我规划去故宫的路线", user_id="user-001")
```

## 3. Go SDK

### 安装

```bash
go get github.com/mindflow/mindflow-map/sdk/go
```

### 使用示例

```go
package main

import (
    "context"
    "fmt"
    "log"

    mindflow "github.com/mindflow/mindflow-map/sdk/go"
)

func main() {
    client := mindflow.NewClient(
        mindflow.WithBaseURL("https://api.mindflow.ai"),
        mindflow.WithAPIKey("your-api-key"),
    )

    // 搜索地点
    result, err := client.Map.Search(context.Background(), &mindflow.MapSearchRequest{
        Query: "中关村",
        City:  "北京",
    })
    if err != nil {
        log.Fatal(err)
    }
    fmt.Printf("搜索结果: %+v\n", result)
}
```

## 4. 生成自定义 SDK

参考 [OPENAPI_SDK_GENERATION.md](../docs/OPENAPI_SDK_GENERATION.md)
