# =============================================================================
# Feishu Bot — Multi-stage production Dockerfile
# Target: minimal attack surface, non-root user, health checks
# =============================================================================

# ---------- Stage 1: builder ----------
FROM python:3.12-slim-bookworm AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libffi-dev \
        libssl-dev \
        procps \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && pip config set global.timeout 120 && pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# ---------- Stage 2: runtime ----------
FROM python:3.12-slim-bookworm AS runtime

# Environment defaults
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy application source
COPY bot.py .
COPY code_runner.py .
COPY codex_api.py .
COPY feishu_consumer.py .
COPY feishu_service.py .
COPY tests/ ./tests/

# Install runtime dependencies (procps for healthcheck pgrep)
RUN apt-get update \
    && apt-get install -y --no-install-recommends procps \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user and workspace
RUN groupadd -r appuser \
    && useradd -r -g appuser -d /app -s /usr/sbin/nologin appuser \
    && mkdir -p /app/workspace \
    && chown -R appuser:appuser /app /opt/venv

# Expose port (Feishu bot uses WebSocket + webhook, no fixed HTTP port)
# Health check via webhook endpoint if configured
EXPOSE 8080

# Switch to non-root user
USER appuser

# Run feishu bot
CMD ["python", "bot.py"]
