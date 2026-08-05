# =============================================================================
# Net-Agent Server - Multi-stage production Dockerfile
# Target: minimal attack surface, non-root user, health checks
# Build context: ghost-main/ (so net_agent_common/ is accessible)
# =============================================================================

# ---------- Stage 1: builder ----------
FROM python:3.12-slim-bookworm AS builder

WORKDIR /build

RUN sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g; s|security.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null; sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g; s|security.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list 2>/dev/null; apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libffi-dev \
        libssl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY net_agent_server/requirements.txt .
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && pip config set global.timeout 120 && pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# ---------- Stage 2: runtime ----------
FROM python:3.12-slim-bookworm AS runtime

LABEL org.opencontainers.image.title="net-agent-server" \
      org.opencontainers.image.description="Ghost Net-Agent — Network operations microservice" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.vendor="Ghost Team"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    NET_AGENT_HOST="0.0.0.0" \
    NET_AGENT_PORT="18180" \
    GATEWAY_URL="http://gateway:18080" \
    ALPHAID_URL="http://alphaid:8000" \
    NEBULA_URL="http://nebula:2002"

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv

# Copy net_agent_server and net_agent_common (sibling directories under ghost-main/)
COPY net_agent_server/ ./net_agent_server/
COPY net_agent_common/ ./net_agent_common/

RUN groupadd -r appuser \
    && useradd -r -g appuser -d /app -s /usr/sbin/nologin appuser \
    && mkdir -p /data \
    && chown -R appuser:appuser /app /data /opt/venv

EXPOSE 18180

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:18180/health')" || exit 1

USER appuser

CMD ["uvicorn", "net_agent_server.main:app", \
     "--host", "0.0.0.0", \
     "--port", "18180", \
     "--log-level", "info", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*"]
