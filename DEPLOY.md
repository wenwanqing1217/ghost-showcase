# MindFlow 项目部署手册

## 当前状态

所有 4 个项目已完成生产级加固，测试全部通过，代码已提交到本地 Git。

| 项目 | 状态 | 测试 | 构建 |
|------|------|------|------|
| mindflow | 已提交，干净 | 16/16 通过 | 通过 |
| DS | 已提交，干净 | 20/20 通过 | 通过 |
| ai综艺 | 已提交，干净 | — | 通过 |
| zcode-brain | 已提交，干净 | 10/10 通过 | 通过 |

## GitHub 推送步骤

### 1. 登录 GitHub CLI

```bash
gh auth login
```

按提示选择 GitHub.com -> HTTPS -> 浏览器授权或粘贴 token。

### 2. 创建仓库

在 `D:\mindflow-workspace` 根目录执行：

```bash
cd D:\mindflow-workspace

# 创建 4 个仓库
gh repo create wenwanqing1217/mindflow --private --source=./mindflow --remote=origin --push
gh repo create wenwanqing1217/DS --private --source=./DS --remote=origin --push
gh repo create wenwanqing1217/ai综艺 --private --source=./ai综艺 --remote=origin --push
gh repo create wenwanqing1217/zcode-brain --private --source=./zcode-brain --remote=origin --push
```

如果已有同名仓库，先删除远端分支冲突或使用 `--public`/`--private` 调整可见性。

### 3. 验证

```bash
gh repo list wenwanqing1217 --limit 10
```

## Vercel 部署步骤

### 前提

- 已安装 Vercel CLI：`npm i -g vercel`
- 已登录：`vercel login`

### 1. DS 部署

```bash
cd D:\mindflow-workspace\DS

# 部署到生产环境
vercel --prod

# 首次部署时添加环境变量
vercel env add OPENAI_API_KEY production
vercel env add SHOPIFY_SHOP_DOMAIN production
vercel env add SHOPIFY_ACCESS_TOKEN production
vercel env add DATABASE_URL production
```

环境变量说明：
- `OPENAI_API_KEY`：OpenAI API 密钥
- `SHOPIFY_SHOP_DOMAIN`：Shopify 店铺域名，如 `your-store.myshopify.com`
- `SHOPIFY_ACCESS_TOKEN`：Shopify Admin API Access Token
- `DATABASE_URL`：PostgreSQL 数据库连接字符串

### 2. ai综艺 部署

```bash
cd D:\mindflow-workspace\ai综艺

# 部署到生产环境
vercel --prod
```

### 3. MindFlow 部署

MindFlow 是 monorepo，需要分别部署 web 和 api。

```bash
cd D:\mindflow-workspace\mindflow

# 部署 API
cd apps/api
vercel --prod --name mindflow-api

# 部署 Web
cd ../web
vercel --prod --name mindflow-web
```

环境变量：
- API：`OPENAI_API_KEY`、`DATABASE_URL`、`PORT`
- Web：`NEXT_PUBLIC_API_URL`（指向 API 地址）

## 统一架构说明

根据 `new/MINDFLOW-AID-FUSION.md`，最终产品架构为：

```
AID（数字身份层）
    ↓ DID 注入
MindFlow（执行层）
    ↓ API 调用
应用层（DS / ai综艺 / 小程序）
```

当前 4 个仓库是 MindFlow 统一平台的 4 个独立应用：
- **mindflow**：核心平台（API + Web）
- **DS**：Shopify 电商自动化应用
- **ai综艺**：前端展示应用
- **zcode-brain**：内部调度系统

## 常见问题

### GitHub CLI 登录失败

如果浏览器授权不可用，使用 token 方式：

```bash
gh auth login --web --git-protocol https
# 或使用 personal access token
gh auth login --with-token < token.txt
```

### Vercel CLI 登录失败

使用 token 方式：

```bash
vercel login --token <your-vercel-token>
```

### 数据库初始化

DS 使用 Prisma，部署后需要运行：

```bash
cd D:\mindflow-workspace\DS
npx prisma migrate deploy
npx prisma db seed
```

## 联系

如有问题，查看各项目 `DEPLOY.md` 获取详细部署说明。
