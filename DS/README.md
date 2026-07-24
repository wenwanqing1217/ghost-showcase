# Ghost DS — 电商运营看板

Ghost × Shoplazza 跨境电商自动化运营数据看板。

## 快速开始

```bash
# 1. 安装依赖
npm install

# 2. 本地开发环境搭建（自动配置 SQLite + 种子数据）
npm run dev:setup

# 3. 启动开发服务器（端口 3004）
npm run dev

# 4. 打开浏览器
open http://localhost:3004
```

## 连接真实店铺

1. 获取 Shoplazza Access Token（后台 → 设置 → API）
2. 在 DS → 店铺设置 → 输入店铺域名和 Token
3. 点击「一键全同步」拉取商品和订单数据

## AI 文案生成

设置环境变量后自动启用：

```bash
AI_API_KEY=your_deepseek_key
AI_BASE_URL=https://api.deepseek.com/v1
AI_MODEL=deepseek-chat
```

在商品列表页点击 ✨ 按钮即可 AI 优化标题和描述。

## 数据库

| 环境 | 数据库 | 切换方式 |
|------|--------|----------|
| 本地开发 | SQLite | 默认（schema.local.prisma） |
| 生产 Docker | PostgreSQL | docker-compose 自动切换 |

切换命令：
```bash
# 本地（SQLite）
cp prisma/schema.local.prisma prisma/schema.prisma && npx prisma db push

# 生产（PostgreSQL）
cp prisma/schema.production.prisma prisma/schema.prisma && npx prisma db push
```

## Docker 部署

```bash
# 构建镜像
docker build -t ghost-ds .

# 运行
docker run -p 3000:3000 --env-file .env ghost-ds
```

## 项目结构

```
DS/
├── prisma/                   # 数据库 schema + 迁移 + 种子
│   ├── schema.prisma         # 当前激活的 schema
│   ├── schema.local.prisma    # SQLite（本地开发）
│   ├── schema.production.prisma # PostgreSQL（生产）
│   └── seed.ts               # Demo 种子数据
├── src/
│   ├── app/                  # Next.js App Router
│   │   ├── page.tsx          # 看板首页
│   │   ├── products/         # 商品管理
│   │   ├── orders/           # 订单管理
│   │   ├── settings/         # 店铺连接
│   │   └── api/              # API 路由
│   ├── components/           # 共享组件
│   └── lib/                  # 核心库
│       ├── shoplazza.ts      # Shoplazza API 客户端
│       ├── ai.ts             # DeepSeek AI 文案服务
│       └── prisma.ts         # Prisma 客户端
├── Dockerfile                # 生产构建
└── package.json
```

## 已实现功能

- [x] 店铺连接（Shoplazza API 验证）
- [x] 商品/订单数据同步（手动触发）
- [x] 看板概览（统计卡片 + 状态分布）
- [x] 商品管理列表（搜索/筛选/分页）
- [x] 订单管理列表（状态标签/筛选）
- [x] AI 商品文案生成（DeepSeek）
- [x] Demo 模式（无需真实店铺数据）
- [x] Docker 部署（standalone 输出）

## 路线图

- [ ] 订单履约流程（MVP3）
- [ ] 数据报表图表（MVP3）
- [ ] 飞书多维表格同步（MVP3）
- [ ] Webhook 实时推送（MVP4）
- [ ] 定时自动同步（MVP4）

## 端口

- 开发：`3004`
- 生产：`3000`
