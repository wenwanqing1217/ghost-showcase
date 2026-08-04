# Ghost DS

Next.js 电商运营看板（L6）。端口 `3001`（外部）/ `3000`（容器内）。

- Prisma + PostgreSQL
- Shoplazza 订单同步
- AI 产品描述生成
- 库存预警

## 启动

```bash
cd DS
cp .env.example .env
npm install
npm run dev        # 开发：localhost:3001
```

Docker Compose: `docker compose up ghost-ds`

## 环境变量

| 变量 | 说明 |
|:-----|:-----|
| `DATABASE_URL` | PostgreSQL 连接串 |
| `REDIS_URL` | Redis 连接串 |
| `NEXT_PUBLIC_GATEWAY_URL` | Gateway 地址 |
| `DEMO_MODE` | 演示模式 |
