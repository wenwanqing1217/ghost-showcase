# ════════════════════════════════════════════════════════════════════
# Ghost DS — Next.js + Prisma 电商看板（生产 Dockerfile）
# ════════════════════════════════════════════════════════════════════

FROM node:20-slim AS base

# Install libssl for Prisma query engine compatibility (Debian)
RUN apt-get update \
    && apt-get install -y --no-install-recommends libssl3 \
    && rm -rf /var/lib/apt/lists/*

# ── 依赖安装（利用 Docker 缓存） ──
FROM base AS deps
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install

# ── 构建（PostgreSQL schema） ──
FROM base AS builder
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# 切换到生产 schema（PostgreSQL）
RUN cp prisma/schema.production.prisma prisma/schema.prisma

# 生成 Prisma Client
ENV NEXT_TELEMETRY_DISABLED=1
RUN npx prisma generate

# 构建 Next.js（standalone 输出）
ENV NEXT_OUTPUT=standalone
RUN npm run build

# ── 运行 ──
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# 创建非 root 用户（Debian 语法）
RUN groupadd -r nodejs && useradd -r -g nodejs -m nextjs

# 复制 standalone 构建产物
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# 复制 prisma schema + CLI（用于启动时迁移）
COPY --from=builder --chown=nextjs:nodejs /app/prisma ./prisma
# prisma CLI 依赖完整 node_modules 上下文（含相对路径 ../package.json 等），
# 因此必须复制完整 node_modules，不能只复制部分文件。
COPY --from=builder --chown=nextjs:nodejs /app/node_modules ./node_modules

USER nextjs
EXPOSE 3000

# 启动时执行数据库迁移，然后启动服务
CMD ["sh", "-c", "npx prisma migrate deploy || npx prisma db push; node server.js"]
