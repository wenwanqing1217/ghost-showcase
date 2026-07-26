# ════════════════════════════════════════════════════════════════════
# Ghost DS — Next.js + Prisma 电商看板（生产 Dockerfile）
# ════════════════════════════════════════════════════════════════════
# 构建：docker build -t ghost-ds .
# 运行：docker run -p 3000:3000 --env-file .env ghost-ds
#
# 注意：构建时自动切换为 PostgreSQL schema（生产环境）
# ════════════════════════════════════════════════════════════════════

FROM node:20-alpine AS base

# ── 依赖安装（利用 Docker 缓存） ──
FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

# ── 构建（PostgreSQL schema） ──
FROM base AS builder
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# 切换到生产 schema（PostgreSQL）
RUN cp prisma/schema.production.prisma prisma/schema.prisma

# 生成 Prisma Client
RUN npx prisma generate

# 构建 Next.js（standalone 输出）
ENV NEXT_TELEMETRY_DISABLED=1
ENV NEXT_OUTPUT=standalone
RUN npm run build

# ── 运行 ──
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# 创建非 root 用户
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# 复制 standalone 构建产物
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# 复制 prisma schema（运行 migrate 用）
COPY --from=builder /app/prisma ./prisma

USER nextjs
EXPOSE 3000

# 启动时执行数据库迁移，然后启动服务
CMD ["sh", "-c", "npx prisma migrate deploy || npx prisma db push; node server.js"]
