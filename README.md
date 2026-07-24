<div align="center">

<h1>
  <img src="https://readme-typing-svg.demolab.com?font=Inter&weight=600&size=32&duration=3000&pause=1000&color=A78BFA&center=true&vCenter=true&width=600&lines=%F0%9F%91%BB+Ghost+%E2%80%94+AI+Agent+Matrix;One+Identity%2C+All+Agents;Digital+You%2C+Everywhere" />
</h1>

<p>
  <img src="https://img.shields.io/github/actions/workflow/status/wenwanqing1217/monorepo/ci.yml?branch=master&style=flat-square&label=CI" alt="CI" />
  <img src="https://img.shields.io/badge/License-MIT-blue?style=flat-square" alt="License: MIT" />
  <img src="https://img.shields.io/badge/Python-3.12+-3776AB?logo=python&style=flat-square&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/TypeScript-5.x-3178C6?logo=typescript&style=flat-square&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&style=flat-square&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/DID-Ed25519-7C3AED?style=flat-square" alt="DID" />
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker&style=flat-square&logoColor=white" alt="Docker" />
</p>

<p>
  <strong>Every AI tool is a stranger. Ghost changes that.</strong><br />
  <em>The identity layer sitting on top of all AI agents.</em>
</p>

</div>

---

> **Ghost is not another AI assistant.** It is the **Ghost Layer** — a unified identity and orchestration matrix that sits on top of every AI tool you use.
>
> Each time you try a new AI tool, it's like meeting a stranger. You introduce yourself. You explain your context. You rebuild your preferences. Ghost ends this fragmentation: **register once, every agent knows you.**

---

## Why Ghost

AI tools are proliferating. Each one is isolated — a silo with no memory of who you are.

Ghost solves this with three primitives:

| Primitive | What it does |
|-----------|--------------|
| **DID Identity** | Ed25519-based decentralized identity. You own your identity, not a platform. |
| **Dual-Chain Memory** | Public chain (shareable) + private chain (AES-256-GCM encrypted). Your memories travel with you. |
| **Agent Orchestration** | MasterAgent + DomainAgents with loop-based execution. One entry point, infinite specialization. |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         User / Client                               │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                     Gateway (Unified API)                           │
│                     :18080                                          │
│                     Auth · Rate Limit · Route · Envelope            │
└──────┬───────────────────────────────────┬──────────────────────────┘
       │                                   │
       ▼                                   ▼
┌──────────────────┐              ┌──────────────────┐
│   Alpha-ID       │              │   Nebula         │
│   Identity Layer │              │   Workflow Engine│
│   :8000          │              │   :2002          │
│                  │              │                  │
│  DID / JWT / jti │              │  LLM Intent      │
│  Dual-Chain Mem  │              │  Multi-Platform  │
│  MCP Protocol    │              │  Vector Search   │
│  Feishu Bot      │              │  Tool Registry   │
└──────────────────┘              └──────────────────┘
       │                                   │
       └──────────────┬────────────────────┘
                      ▼
           ┌──────────────────┐
           │   PostgreSQL     │
           │   :5432          │
           └──────────────────┘
```

### Five-Layer Model

| Layer | Name | Status |
|-------|------|--------|
| **L5** | Ecosystem — Plugin market, Agent exchange, Governance | Planned |
| **L4** | Economy — Ghost Key, Proof of Execution, Service pricing | Planned |
| **L3** | Platform — Multi-tenant, Plugin system, Observability | In progress |
| **L2** | Agent Intelligence — MasterAgent, DomainAgents, Loop engine, Memory | Live |
| **L1** | Infrastructure — LLM gateway, PostgreSQL, Encryption, Monitoring | Live |

---

## Quickstart

```bash
# Clone (with submodules)
git clone --recurse-submodules https://github.com/wenwanqing1217/monorepo.git
cd monorepo

# One-command start (PostgreSQL + Alpha-ID + Nebula + Gateway)
cp .env.example .env
docker compose up -d

# Open browser
#   Gateway (Unified API)  → http://localhost:18080
#   Alpha-ID (Identity)    → http://localhost:8000
#   Nebula (Workflow)      → http://localhost:2002
```

Or run individual services:

```bash
# Identity Layer (PyPI published)
pip install alpha-id
aid init && aid detect && aid profile show

# From source
cd alphaid/projects && pip install -e ".[dev]"
uvicorn src.main:app --reload --port 8000

# Workflow Engine
cd nebula && pip install -e ".[dev]"
uvicorn mindflow_map.main:app --reload --port 2002
```

---

## Projects

| Project | Role | Stack | Tests |
|---------|------|-------|-------|
| **[alpha-id](https://github.com/wenwanqing1217/alpha-id)** | Identity Layer | Python + FastAPI | 928 |
| **[zcode-brain](https://github.com/wenwanqing1217/zcode-brain)** | Orchestration | TypeScript + Node | 42 |
| **[mindflow-map](https://github.com/wenwanqing1217/mindflow-map)** | Workflow Engine | Python + FastAPI | 221 |
| **[mindflow](https://github.com/wenwanqing1217/mindflow)** | Frontend Portal | Next.js | 32 |
| **ghost-main/gateway** | Unified API Gateway | Python + FastAPI | — |

---

## Tech Stack

```
Language:    Python · TypeScript · SQL
Backend:     FastAPI · SQLAlchemy · Alembic · PostgreSQL · Redis
Frontend:    Next.js 14 · React 18 · Tailwind
AI:          MCP Protocol · LLM Gateway · DeepSeek · ReAgent · TwinBrain
Identity:    DID (Ed25519) · JWT with jti revocation · Skill Signing
Infra:       Docker · Caddy · Prometheus · GitHub Actions
Channels:    Feishu · WeChat · Douyin · Baidu Maps
```

---

## Security

- **JWT + jti revocation** — Every token has a unique ID; logout revokes instantly
- **Rate limiting** — Sliding window per-IP (5 req/60s for sensitive endpoints)
- **Token rotation** — Refresh tokens are single-use; rotation detects reuse
- **AES-256-GCM** — Private memory chain encrypted at rest
- **Ed25519 DID** — Client-side key generation via Web Crypto API
- **CORS allowlist** — Explicit origin whitelist, not `*`
- **No hardcoded secrets** — All credentials via environment variables

See [SECURITY.md](./SECURITY.md) for full details.

---

## Roadmap

### Phase 0: Foundation ✅
- [x] Identity Layer (Alpha-ID) — PyPI published
- [x] Workflow Engine (Nebula)
- [x] Orchestration Layer (core)
- [x] Unified API Gateway
- [x] Docker Compose one-command deploy

### Phase 1: Core 🚧
- [ ] Unify Feishu conversation paths
- [ ] Security hardening (credentials → env vars)
- [ ] CI stabilization
- [ ] MasterOrchestrator rewrite

### Phase 2: Platform 📋
- [ ] Event bus (Message Bus)
- [ ] Multi-tenant engine
- [ ] Persistence layer (Prisma + PostgreSQL)
- [ ] A2A real communication protocol

### Phase 3: Economy 🔮
- [ ] Ghost Key 2.0
- [ ] Proof of Execution
- [ ] Service pricing & settlement

### Phase 4: Ecosystem 🔮
- [ ] Agent exchange
- [ ] Community governance
- [ ] Open API + SDK

---

## Contributing

```bash
git clone --recurse-submodules https://github.com/YOUR_NAME/monorepo.git
cd monorepo

# Install pre-commit hooks
pip install pre-commit && pre-commit install

# Start dev environment
docker compose up -d db
cd alphaid/projects && pip install -e ".[dev]" && uvicorn src.main:app --reload

# Run tests
pytest tests/ -v --tb=short --cov=src --cov-report=term-missing
```

Commit convention: `feat:` · `fix:` · `docs:` · `refactor:` · `test:` · `chore:`

Lint: Python `ruff` / TypeScript `eslint + prettier`

---

## License

[MIT](./LICENSE)

---

<div align="center">

<sub>Ghost — The identity layer sitting on top of all AI tools.</sub><br />
<sub>Register once. Every agent knows you.</sub>

</div>
