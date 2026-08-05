# =============================================================================
# AgentOrchestrator - Production Dockerfile
# Target: minimal attack surface, non-root user, health checks
# =============================================================================

FROM python:3.12-slim-bookworm AS builder

WORKDIR /build

RUN sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g; s|security.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null; sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g; s|security.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list 2>/dev/null; apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY orchestrator/requirements.txt .
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && pip config set global.timeout 120 && pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt

# ---------- Stage 2: runtime ----------
FROM python:3.12-slim-bookworm AS runtime

LABEL org.opencontainers.image.title="agent-orchestrator" \
      org.opencontainers.image.description="Ghost AgentOrchestrator — 双编程工具协同调度中枢" \
      org.opencontainers.image.version="1.0.0" \
      org.opencontainers.image.vendor="Ghost Team"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    ORCHESTRATOR_HOST="0.0.0.0" \
    ORCHESTRATOR_PORT="19090" \
    GATEWAY_URL="http://gateway:18080"

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv

COPY orchestrator/main.py ./

# 完整集成 OrchestratorEngine：打包 alphaid 的 core（事件总线/TwinBrain/settings）
# 与 orchestrator 包（engine.py），让 _HAS_ENGINE=True 恢复后台循环（Memory/Ops/Social/OPTIMAL_SWAP）。
COPY alphaid/projects/src/core ./core
COPY alphaid/projects/src/orchestrator ./orchestrator

RUN groupadd -r appuser \
    && useradd -r -g appuser -d /app -s /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app /opt/venv

EXPOSE 19090

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:19090/health')" || exit 1

USER appuser

# 安全: 仅信任 Docker 内部网关 (172.16.0.0/12) 的代理头
# 生产环境应替换为实际反向代理 IP
CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "19090", \
     "--log-level", "info", \
     "--proxy-headers", \
     "--forwarded-allow-ips", "172.16.0.0/12"]
