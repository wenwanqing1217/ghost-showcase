# Ghost Platform — Architecture Design

> Self-contained architecture document based on actual codebase analysis.

---

## System Topology

### Conversation Paths

```
                     User
                     │
                     ▼
            ┌───────────────────┐
            │ Gateway (Unified) │
            │ :18080            │
            └────────┬──────────┘
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
┌──────────────────┐   ┌──────────────────┐
│   Alpha-ID       │   │   Nebula         │
│   Identity       │   │   Workflow       │
│   :8000          │   │   :2002          │
│                  │   │                  │
│  DID / JWT / jti │   │  LLM Intent      │
│  Dual-Chain Mem  │   │  Multi-Platform  │
│  MCP Protocol    │   │  Vector Search   │
│  Feishu Bot      │   │  Tool Registry   │
└──────────────────┘   └──────────────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
           ┌──────────────────┐
           │   PostgreSQL     │
           │   :5432          │
           └──────────────────┘
```

### Module Status

| Module | Files | Function | Key Capabilities |
|--------|-------|----------|------------------|
| alphaid/projects/ | ~15 | Identity, AgentLoop, TwinBrain | 14 tools, dual-chain memory, A2A |
| nebula/ | 75+ | Workflow engine, LLM gateway | Multi-platform, vector search, tool registry |
| core/ | 21 | Dispatcher, safety guardrails | 12 role configs, permission gating |
| flow/ | ~30 | Frontend portal, Ghost Key | 6 AI providers, dual-chain memory |
| ghost-main/gateway/ | ~5 | Unified API gateway | Auth, rate limit, routing, envelope |

---

## Five-Layer Model

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Layer 5: Ecosystem                                                     │
│  Plugin market │ Agent exchange │ Governance │ Open API                 │
├─────────────────────────────────────────────────────────────────────────┤
│  Layer 4: Economy                                                       │
│  Ghost Key 2.0 │ Proof of Execution │ Service pricing │ Incentives     │
├─────────────────────────────────────────────────────────────────────────┤
│  Layer 3: Platform                                                      │
│  Multi-tenant │ Plugin system │ Event bus │ Observability │ Isolation  │
├─────────────────────────────────────────────────────────────────────────┤
│  Layer 2: Agent Intelligence                                            │
│  MasterAgent │ DomainAgents │ Loop engine │ Memory │ A2A communication │
├─────────────────────────────────────────────────────────────────────────┤
│  Layer 1: Infrastructure                                                │
│  LLM gateway │ Database │ Message queue │ Encryption │ Monitoring      │
└─────────────────────────────────────────────────────────────────────────┘
```

### Layer 1: Infrastructure

```
LLM Gateway (unified LLM entry)
├── DeepSeek / OpenAI / Anthropic / Local models
├── Circuit breaker: auto-failover on provider outage
├── Rate limiting: Token Bucket to prevent quota exhaustion
└── Caching: deduplicate identical queries

Database Layer
├── PostgreSQL: user data, transactions
├── Redis: sessions, caching, rate limiting
├── VectorDB (pgvector/Milvus): memory vector search
└── File storage: images, attachments

Security Vault
├── Key management (no hardcoded secrets)
├── End-to-end encryption
└── Audit logging
```

### Layer 2: Agent Intelligence

```
Agent Runtime
├── MasterAgent (per-user singleton)
│   ├── IntentClassifier (LLM-based, not keyword)
│   ├── TaskDecomposer
│   ├── ToolDispatcher
│   └── ResponseAggregator
│
├── DomainAgents
│   ├── MemoryAgent — read/write/organize/forget
│   ├── SocialAgent — social interactions, friends, A2A
│   ├── OpsAgent — project operations, data sync
│   ├── CreateAgent — content creation
│   └── [Extensible]
│
├── Loop Engine
│   ├── MasterLoop: triggered per message
│   ├── MemoryLoop: every 5 minutes
│   ├── OpsLoop: every 30 minutes
│   └── SocialLoop: event-driven
│
└── Memory System
    ├── Short-term: current conversation (Redis)
    ├── Mid-term: recent memories (PostgreSQL)
    ├── Long-term: core identity (VectorDB)
    └── Dual-chain: public + private (AES-256-GCM)
```

### Layer 3: Platform

```
Multi-Tenant Engine
├── Each user = independent Agent instance
├── Resource quotas: LLM calls, storage, tools
├── Isolation: user A's data invisible to user B
└── Shared: public tools, public knowledge base

Channel Adapter (channel abstraction)
├── FeishuAdapter
├── WebAdapter
├── WeChatAdapter (future)
├── TelegramAdapter (future)
└── [Any new channel] → implement Adapter interface

Observability
├── Agent Trace: full decision chain per interaction
├── Metrics: response time, tool calls, success rate
├── Debug Console: real-time Agent state inspection
└── Alert: auto-notify on anomalies
```

### Layer 4: Economy

```
Ghost Key 2.0
├── Identity key: proves "you are you"
├── Service key: access specific features
├── Invite key: reward for inviting new users
└── Governance key: community voting rights

Proof of Execution (PoE)
├── Every Agent execution generates a proof
├── Optional on-chain verification
└── Contribution metrics: how much you helped others
```

### Layer 5: Ecosystem

```
Agent Exchange
├── Publish your Agent capabilities
├── Discover others' Agent services
├── Auto-match supply ↔ demand
└── Trust scoring (based on PoE)

Community Governance
├── Proposal system
├── Voting mechanism (based on governance keys)
├── Dispute arbitration
└── Protocol upgrades
```

---

## Key Architecture Decisions

### Decision 1: Event-Driven > Direct Calls

```
# Tight coupling (anti-pattern)
agent.run() → memory.write() → social.notify() → log.record()

# Event-driven (target)
agent.run() → emit("agent.action.completed")
              ├── memory.subscribe → write()
              ├── social.subscribe → notify()
              ├── log.subscribe → record()
              └── [future module] subscribe → do_something()
```

Benefit: adding new features doesn't require modifying old code — just subscribe to events.

### Decision 2: Channel Adapter > Channel Hardcoding

```
ChannelAdapter (abstraction)
├── FeishuAdapter
├── WebAdapter
├── WeChatAdapter (future)
├── TelegramAdapter (future)
└── [Any new channel] → implement Adapter interface
```

### Decision 3: Multi-Tenant from Day One

```
All tables:
  id | tenant_id | ...fields | created_at | updated_at

All APIs:
  middleware: extract tenant_id from token
  query: WHERE tenant_id = ?
```

### Decision 4: LLM Gateway Abstraction

```
LLMGateway
├── Current: DeepSeek (primary) + OpenAI (fallback)
├── Future: local models (privacy scenarios)
├── Future: multi-model routing (cheap for simple, powerful for complex)
└── Future: model marketplace (user choice)
```

---

## A2A Communication Protocol

```
Agent A → POST /a2a/call
{
  "caller": "Alpha-1",
  "target": "Alpha-3",
  "skill": "generate_content",
  "params": {"topic": "AI Agent"},
  "proof": "<Ed25519 signature>"
}

Agent B → Response
{
  "result": "...",
  "proof": "<execution proof>",
  "timestamp": 1721800000
}
```

---

## Loop Design

| Loop | Responsibility | Trigger | Frequency |
|------|---------------|---------|-----------|
| MasterLoop | Global task scheduling, intent routing | Per user message | Real-time |
| MemoryLoop | Memory organization, forgetting, association | Scheduled/triggered | Every 5 min |
| OpsLoop | Project operations, data sync | Scheduled | Every 30 min |
| SocialLoop | Social interaction, A2A communication | Event-driven | Real-time |

---

## Evolution Roadmap

### Phase 0: Foundation (Complete)
- Identity Layer (Alpha-ID) — PyPI published
- Workflow Engine (Nebula)
- Orchestration Layer (core)
- Unified API Gateway
- Docker Compose one-command deploy

### Phase 1: Core (In Progress)
- Unify Feishu conversation paths
- Security hardening
- CI stabilization
- MasterOrchestrator rewrite

### Phase 2: Platform
- Event bus
- Multi-tenant engine
- Persistence layer
- A2A real communication

### Phase 3: Economy
- Ghost Key 2.0
- Proof of Execution
- Service pricing

### Phase 4: Ecosystem
- Agent exchange
- Community governance
- Open API + SDK

---

*Version: 2.0*
*Date: 2026-07-24*
*Based on: full codebase audit*
