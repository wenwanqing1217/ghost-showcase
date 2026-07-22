# MindFlow Map 部署指南

## 1. 本地启动

```bash
cd mindflow-map
pip install -e ".[dev]"
playwright install chromium
cp .env.example .env
uvicorn mindflow_map.main:app --reload --port 2002
```

## 2. 环境变量

| 变量 | 说明 | 必填 |
|------|------|------|
| FEISHU_APP_ID | 飞书应用 ID | 是 |
| FEISHU_APP_SECRET | 飞书应用密钥 | 是 |
| BAIDU_MAP_AUTH_TOKEN | 百度地图 Agent Plan Token | 是 |
| OPENAI_API_KEY | DeepSeek/豆包 API Key | 是 |
| ALPHA_ID_API_URL | Alpha-ID 服务地址 | 否 |
| DOUYIN_USERNAME | 抖音账号 | 否 |
| DOUYIN_PASSWORD | 抖音密码 | 否 |
| SHOPIFY_SHOP_DOMAIN | Shopify 域名 | 否 |
| SHOPIFY_ACCESS_TOKEN | Shopify Token | 否 |

## 3. 飞书机器人配置

1. 打开 https://open.feishu.cn/
2. 创建企业自建应用
3. 开启机器人能力
4. 添加事件：`im.message.receive_v1`（接收消息）
5. 在应用凭证页复制 App ID 和 App Secret
6. 发布应用
7. MindFlow 使用长连接模式，无需公网域名或回调地址

## 4. 百度地图 Agent Plan 配置

1. 打开 https://lbs.baidu.com/apiconsole/agentplan
2. 创建应用，获取 `baidu_map_auth_token`
3. 将 Token 填入 .env

## 5. Vercel 部署

```bash
vercel --prod
```

环境变量在 Vercel Dashboard 中配置。
