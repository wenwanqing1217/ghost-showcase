# 用户操作指南

## 你需要做的（只需 5 步）

### Step 1: 创建飞书机器人（5分钟）

1. 访问 [飞书开放平台](https://open.feishu.cn/)
2. 点击「创建企业自建应用」
3. 填写应用名称：`MindFlow Assistant`
4. 进入应用，开启「机器人」能力
5. 添加事件：`im.message.receive_v1`（接收消息）
6. 记录以下信息：
   - **App ID**
   - **App Secret**
   - **Verification Token**
   - **Encrypt Key**
7. 发布应用
8. MindFlow 使用长连接模式，无需公网域名或回调地址

### Step 2: 申请百度地图 Agent Plan Token（5分钟）

1. 访问 [百度地图 Agent Plan 控制台](https://lbs.baidu.com/apiconsole/agentplan)
2. 注册/登录账号
3. 进入「应用管理」→「创建应用」
4. 填写应用名称：`MindFlow Map`
5. 复制 **baidu_map_auth_token**
6. 将 Token 填入 `.env`

### Step 3: 申请 DeepSeek API Key（5分钟）

1. 访问 [DeepSeek 开放平台](https://platform.deepseek.com/)
2. 注册/登录
3. 进入「API Keys」→「创建 API Key」
4. 复制 Key（只显示一次）

### Step 4: 提供抖音短剧账号（可选）

- 提供账号密码或授权我们自动登录
- 或者你自己登录，我们通过 Computer Use 操作

### Step 5: 提供 Shopify 店铺（可选）

- 提供店铺域名和 Access Token
- 或者我们先做 Demo，不接入真实店铺

---

## 把信息发给我

把以上 Step 1-3 的信息整理成下面格式：

```
飞书 App ID: xxx
飞书 App Secret: xxx
百度地图 Auth Token: xxx
DeepSeek API Key: xxx
抖音账号: xxx（可选）
Shopify: xxx（可选）
```

我会立刻：
1. 配置环境变量
2. 启动服务
3. 测试连接
4. 你在飞书就能跟我对话了

---

## 常见问题

**Q: 我没有飞书企业账号怎么办？**
A: 用个人手机号注册飞书，创建个人团队即可。

**Q: 百度地图 Auth Token 申请要多久？**
A: 即时，填写表单后立即生效。

**Q: DeepSeek API 免费吗？**
A: 新用户送 5000万 token，约 3000 次对话，够用很久。

**Q: 抖音短剧自动发布安全吗？**
A: 用 Playwright 模拟人工操作，不破解平台，只是自动化你的操作流程。

**Q: 我中途想改需求怎么办？**
A: 直接跟我说，我随时调整。

**Q: 成本超了怎么办？**
A: 每个服务都有免费额度，超出前我会提前告知你。
