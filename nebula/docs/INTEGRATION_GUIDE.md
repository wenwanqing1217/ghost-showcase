# MindFlow 集成指南

## 1. 总览

MindFlow 不是一个封闭的聊天应用，而是一个**工作流引擎**。你可以用多种前端（WeChat、Feishu、Web Chat）去调用它。

```
用户消息来源 → 消息适配器 → MindFlow 工作流引擎 → 结果返回
```

---

## 2. 现有集成方案（已就绪）

### 2.1 飞书（Feishu）— **推荐，最快可用**

| 项目 | 状态 |
|------|------|
| App ID / Secret | 已配置 |
| 事件订阅 | 已实现 |
| 用户鉴权 | 已接入 Alpha-ID |
| 部署 | 无需额外服务器，`webhook` 直连 |

**对接方式：**
1. 登录 [飞书开放平台](https://open.feishu.cn/) → 创建自建应用
2. 开启机器人能力 → 设置 Request URL 指向你的 MindFlow 服务
3. 用户向机器人发消息，MindFlow 自动回复

### 2.2 Web 聊天（Web Chat）— **零配置，即时可用**

MindFlow Map 前端自带聊天入口，部署后用户可直接在浏览器中交互。

- 优点：无需申请账号，无需审核
- 缺点：仅限桌面端，无法推送离线消息

---

## 3. 微信公众号方案

微信公众号需要**独立部署一个消息适配层**，推荐方案如下：

### 3.1 架构图

```
微信公众号服务器
    ↓ XML 消息
MindFlow /api/v1/wechat (mindflow-map 项目)
    ↓ 调用工作流
Alpha-ID / DeepSeek / 其他服务
    ↓ 回复
微信公众号 → 用户
```

### 3.2 前置条件

| 环境变量 | 说明 | 获取方式 |
|----------|------|----------|
| `WECHAT_TOKEN` | 消息校验 Token，自定义字符串 | 自己设一个随机字符串 |
| `WECHAT_APP_ID` | 公众号 AppID | 微信公众平台后台 |
| `WECHAT_APP_SECRET` | 公众号 AppSecret | 微信公众平台后台 |
| `WECHAT_AES_KEY` | 消息加密密钥（安全模式必须） | 公众平台后台 → 基本配置 |

### 3.3 部署步骤

1. **准备服务器**（需有公网 IP，80/443 端口可访问）
2. **配置环境变量**
   ```bash
   # mindflow-map/.env
   WECHAT_TOKEN=your-custom-token
   WECHAT_APP_ID=wx1234567890abcdef
   WECHAT_APP_SECRET=abcdef1234567890
   WECHAT_AES_KEY=your-43-char-aes-key-generated-by-wechat
   ```
3. **配置公众号服务器**
   - URL: `https://your-domain.com/api/v1/wechat`
   - Token: 与 `WECHAT_TOKEN` 一致
   - 消息加密：安全模式（推荐）或兼容模式
4. **验证服务器**：公众平台点击"提交"验证通过后，消息即可流转

### 3.4 注意事项

- 公众号消息有 5 秒响应限制，MindFlow 工作流超过 5 秒需返回空响应，再用客服消息接口异步回复
- 需在公众号后台设置"自动回复"为关闭，避免冲突

---

## 4. 关于"微信里的机器人对接"

你提到的"手机端机器人"，是微信内置的 **AI 助手（智能体）** 功能，目前：
- **不支持外部 API 调用**
- **无法直接对接 MindFlow 工作流**
- 数据封闭在微信生态内

**替代方案：**
- 如果你想保留微信入口 → 走微信公众号方案（3.3 节）
- 如果你要更开放的 AI 能力 → 飞书（2.1 节）或 Web Chat（2.2 节）

---

## 5. 环境变量清单（全项目）

| 变量 | 项目 | 用途 |
|------|------|------|
| `WECHAT_TOKEN` | mindflow-map | 公众号消息校验 |
| `WECHAT_APP_ID` | mindflow-map | 公众号身份 |
| `WECHAT_APP_SECRET` | mindflow-map | 公众号 API 密钥 |
| `FEISHU_APP_ID` | mindflow-map | 飞书应用 ID |
| `FEISHU_APP_SECRET` | mindflow-map | 飞书应用密钥 |
| `AUTH_MASTER_KEY` | AID | JWT 签名主密钥（必须） |
| `AID_ALLOWED_ORIGINS` | AID | CORS 白名单 |
| `OPENAI_BASE_URL` | AID | LLM 地址（已做 SSRF 防护） |
| `DS_API_KEY` | DS | DS 项目 API 鉴权 |
| `BAIDU_MAP_AUTH_TOKEN` | DS | 百度地图 API Token |
| `SHOPIFY_SHOP_DOMAIN` | DS | Shopify 店铺域名 |
| `SHOPIFY_ACCESS_TOKEN` | DS | Shopify API Token |
| `COMPUTER_USE_ENABLED` | mindflow | 启用/禁用电脑控制功能 |
| `COMPUTER_USE_API_KEY` | mindflow | 电脑控制功能鉴权 |

---

## 6. 快速检查清单

- [ ] 飞书机器人已配置并测试通过
- [ ] Web Chat 前端可正常访问
- [ ] 如需微信公众号，`WECHAT_*` 环境变量已配置
- [ ] Alpha-ID 服务运行中（`http://localhost:2002` 或生产地址）
- [ ] DS 项目 `.env` 已从 Git 移除，使用 `.env.example` 作为模板
- [ ] 各项目 `DS_API_KEY` / `AUTH_MASTER_KEY` 已设置

---

## 7. 常见问题

**Q: 微信公众号和飞书机器人能不能同时用？**
A: 可以，MindFlow 的多通道适配层已就绪，两者消息并行处理。

**Q: 微信 AI 助手能对接 MindFlow 吗？**
A: 目前微信内置 AI 助手不开放外部 API 调用，建议使用飞书或公众号方案。

**Q: 公众号消息回复超时怎么办？**
A: 5 秒内先返回空响应，再通过 `https://api.weixin.qq.com/cgi-bin/message/custom/send` 异步发送客服消息。
