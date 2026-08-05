# =============================================================================
# MindFlow API - Multi-stage production Dockerfile
# Target: minimal Node.js image for Fastify backend
# =============================================================================

# ---------- Stage 1: builder ----------
FROM node:20-alpine AS builder

WORKDIR /build

# Copy workspace definition and ALL workspace package.json files first
COPY package.json ./
COPY apps/api/package.json ./apps/api/
COPY packages/shared/package.json ./packages/shared/

# Copy full workspace source
COPY apps/api/ ./apps/api/
COPY packages/shared/ ./packages/shared/

# Replace workspace:* with file: protocol for reliable Docker builds
RUN sed -i 's/"@mindflow\/shared": "workspace:\*"/"@mindflow\/shared": "file:.\/packages\/shared"/' apps/api/package.json

# Install all dependencies (including dev for build)
RUN npm install --ignore-scripts

# Build (type-check only, tsx runs TS directly)
RUN npm run build -w apps/api

# ---------- Stage 2: runtime ----------
FROM node:20-alpine AS runtime

# Labels
LABEL org.opencontainers.image.title="mindflow-api" \
      org.opencontainers.image.description="MindFlow API — Fastify backend" \
      org.opencontainers.image.version="0.1.0" \
      org.opencontainers.image.vendor="Ghost Team"

# Environment defaults
ENV NODE_ENV=production \
    PORT=3036 \
    HOST=0.0.0.0 \
    LOG_LEVEL=info

WORKDIR /app

# Copy workspace definition and ALL workspace package.json files
COPY package.json ./
COPY apps/api/package.json ./apps/api/
COPY packages/shared/package.json ./packages/shared/

# Copy full workspace source
COPY apps/api/ ./apps/api/
COPY packages/shared/ ./packages/shared/

# Replace workspace:* with file: protocol for reliable Docker builds
RUN sed -i 's/"@mindflow\/shared": "workspace:\*"/"@mindflow\/shared": "file:.\/packages\/shared"/' apps/api/package.json

# Install production dependencies only (file: protocol works without --workspaces flag)
RUN npm install --omit=dev --ignore-scripts

# Create non-root user
RUN addgroup -S appgroup && adduser -S appuser -G appgroup \
    && chown -R appuser:appgroup /app

# Expose port
EXPOSE 3036

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD node -e "fetch('http://localhost:3036/health').then(r=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"

# Switch to non-root user
USER appuser

# Run the API
CMD ["npm", "run", "start", "-w", "apps/api"]
