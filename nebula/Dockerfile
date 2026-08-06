# =============================================================================
# MindFlow Map - Multi-stage production Dockerfile
# Target: minimal attack surface, non-root user, health checks
# =============================================================================

# ---------- Stage 1: builder ----------
FROM python:3.12-slim-bookworm AS builder

WORKDIR /build

# Install build dependencies
RUN sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g; s|security.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null; sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g; s|security.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list 2>/dev/null; apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libffi-dev \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies (includes dev deps for mypy/ruff if needed)
COPY pyproject.toml .
COPY src/ ./src/
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && pip config set global.timeout 120 && pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -e ".[dev]"

# ---------- Stage 2: runtime ----------
FROM python:3.12-slim-bookworm AS runtime

# Labels for image metadata
LABEL org.opencontainers.image.title="mindflow-map" \
      org.opencontainers.image.description="MindFlow Map - AI智能地图助理" \
      org.opencontainers.image.version="0.1.0" \
      org.opencontainers.image.vendor="MindFlow Team"

# Environment defaults
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH="/app/src" \
    # Default to sqlite file in /data; override with DATABASE_URL in prod
    DATABASE_URL="sqlite+aiosqlite:///data/mindflow_map.db" \
    # uvicorn defaults
    UVICORN_HOST=0.0.0.0 \
    UVICORN_PORT=2002 \
    UVICORN_WORKERS=4 \
    UVICORN_LOG_LEVEL=info

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application source
COPY src/ ./src/
COPY README.md ./
COPY alembic.ini ./
COPY alembic/ ./alembic/

# Install playwright chromium (Douyin automation) + system deps
# 浏览器装到 /ms-playwright（非 root appuser 可读）
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
RUN sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g; s|security.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null; sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g; s|security.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list 2>/dev/null; apt-get update \
    && python -m playwright install --with-deps chromium \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user and data directory
RUN groupadd -r appuser \
    && useradd -r -g appuser -d /app -s /usr/sbin/nologin appuser \
    && mkdir -p /data \
    && chown -R appuser:appuser /app /data /opt/venv /ms-playwright

# Expose ports
# 2002: HTTP API
# 9090: Prometheus metrics (if enabled)
EXPOSE 2002

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:2002/health/livez')" || exit 1

# Switch to non-root user
USER appuser

# Run uvicorn
CMD ["uvicorn", "mindflow_map.main:app", \
     "--host", "0.0.0.0", \
     "--port", "2002", \
     "--workers", "4", \
     "--log-level", "info", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*"]
