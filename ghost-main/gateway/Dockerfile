# =============================================================================
# Ghost Gateway - Multi-stage production Dockerfile
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

# Labels for image metadata
LABEL org.opencontainers.image.title="ghost-gateway" \
      org.opencontainers.image.description="Ghost Unified API Gateway" \
      org.opencontainers.image.version="2.0.0" \
      org.opencontainers.image.vendor="Ghost Team"

# Environment defaults
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    # Service URLs (override in docker-compose or k8s)
    ALPHAID_URL="http://alphaid:8000" \
    NEBULA_URL="http://nebula:2002" \
    ORCHESTRATOR_URL="http://orchestrator:19090" \
    FLOW_URL="http://flow:3036" \
    NETAGENT_URL="http://netagent:18180" \
    GATEWAY_PORT="18080" \
    ENVIRONMENT="production" \
    ENABLE_DOUBAO_SCANNER="0" \
    # uvicorn defaults
    UVICORN_HOST="0.0.0.0" \
    UVICORN_PORT="18080" \
    UVICORN_WORKERS="2" \
    UVICORN_LOG_LEVEL="info"

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv

# Copy gateway source
COPY app.py config.py ./
COPY middleware/ ./middleware/
COPY routes/ ./routes/
COPY services/ ./services/
COPY static/ ./static/
COPY entrypoint.sh ./

# Create non-root user and game storage directory
RUN groupadd -r appuser \
    && useradd -r -g appuser -d /app -s /usr/sbin/nologin appuser \
    && mkdir -p /app/generated_games \
    && chown -R appuser:appuser /app /opt/venv /app/generated_games \
    && chmod +x /app/entrypoint.sh

# Expose port
EXPOSE 18080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:18080/health')" || exit 1

# Switch to non-root user
USER appuser

# Run uvicorn via entrypoint (fixes volume permissions)
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["uvicorn", "app:app", \
     "--host", "0.0.0.0", \
     "--port", "18080", \
     "--workers", "2", \
     "--log-level", "info", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "*"]
