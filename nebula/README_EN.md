# MindFlow Map

**AI Unified Workflow Engine | Feishu/WeChat/MP Multi-Platform | Baidu Map Agent Plan | Douyin Short Drama Automation | Shopify E-Commerce Ops**

![Tests](https://img.shields.io/badge/tests-218%2F218%20passing-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

> **One-line pitch**: You talk in Feishu/WeChat, MindFlow automatically checks maps, plans routes, publishes short dramas, and runs your shop — all platforms unified in one workspace.
>
> **Differentiator**: More than workflow automation, MindFlow can autonomously scan code, generate fixes, run tests, and commit to Git — the only AI workflow engine with "self-evolution" capability.

---

## Why MindFlow Map?

| Capability | MindFlow Map | n8n | Feishu/WeCom | AutoGen / CrewAI |
|------------|-------------|-----|--------------|------------------|
| Multi-platform messaging | Feishu long-poll + WeChat webhook + MP | ❌ | Own ecosystem only | ❌ |
| Real map agent | Baidu Map Agent Plan deep integration | ❌ | ❌ | ❌ |
| Autonomous code repair | Self-Loop scan → fix → test → commit | ❌ | ❌ | ❌ |
| Short drama AI pre-check | Local AI scan + platform submit + callback | ❌ | ❌ | ❌ |
| Zero-config trial | `DEMO_MODE=true` to run | ❌ Docker required | ❌ SaaS | ❌ API Key required |
| Chinese ecosystem native | Feishu/WeChat/Douyin/Baidu full stack | ❌ | China only | ❌ |
| Extensible tools | Tool registry + declarative YAML workflows | 400+ nodes | Closed | LangChain tools |
| Streaming execution | SSE real-time workflow progress | ❌ | ❌ | ❌ |
| Multi-level approval | Custom approval chains + history | ❌ | Basic | ❌ |
| Multi-tenant RBAC | Tenant isolation + role permissions + Token auth | ❌ | Basic | ❌ |
| Audit logging | Full-chain operation audit + filterable query | ❌ | ❌ | ❌ |
| Production middleware | Rate limit, CORS, unified error response, health checks | Partial | Partial | ❌ |

---

## Quick Start

### Requirements

- Python 3.10+
- pip
- (Optional) Playwright + Chromium, for Douyin automation

### One-command start (demo mode)

```bash
git clone https://github.com/<your-org>/mindflow-map.git
cd mindflow-map

pip install -e .

# Demo mode: no API keys needed
export DEMO_MODE=true    # Linux/macOS
# or Windows PowerShell: $env:DEMO_MODE=true

uvicorn mindflow_map.main:app --host 0.0.0.0 --port 2002
```

### Access

| Service | Address |
|---------|---------|
| Workspace | http://localhost:2002/workspace |
| Visual Workflow Editor | http://localhost:2002/editor |
| API Docs | http://localhost:2002/docs |
| Health Check | http://localhost:2002/health |

---

## Testing

```bash
# Full test suite (218 passed)
pytest tests/ -v

# Unit tests only
pytest tests/unit/ -v

# With coverage report
pytest tests/ --cov=mindflow_map --cov-report=html
```

---

## Roadmap

- [x] Phase 1: Basic architecture + Feishu long-poll
- [x] Phase 2: Baidu Map Agent Plan integration
- [x] Phase 3: MindFlow Workspace unified dashboard
- [x] Phase 4: WeChat Official Account integration
- [x] Phase 5: Douyin short drama pre-check + automation
- [x] Phase 6: Autopilot autonomous development system
- [x] Phase 7: Visual Workflow Editor (drag-and-drop)
- [x] Phase 8: Plugin SDK + Integration Marketplace
- [x] Phase 9: Multi-Tenancy + RBAC + Audit Logs + Production middleware
- [ ] Phase 10: English docs + i18n

---

## License

MIT
