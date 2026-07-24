# Contributing to Ghost

Thank you for your interest in Ghost. This document helps you get started with contributions.

---

## Development Setup

### Prerequisites

- Python 3.12+
- Node.js 20+
- Docker + Docker Compose
- Git (with submodule support)

### Quickstart

```bash
# 1. Clone (with submodules)
git clone --recurse-submodules https://github.com/wenwanqing1217/monorepo.git
cd monorepo

# 2. Install pre-commit hooks
pip install pre-commit
pre-commit install

# 3. Start infrastructure (PostgreSQL)
docker compose up -d db

# 4. Start the module you want to develop

# ── Identity Layer (Alpha-ID) ──
cd alphaid/projects
pip install -e ".[dev]"
uvicorn src.main:app --reload --port 8000

# ── Workflow Engine (Nebula) ──
cd nebula
pip install -e ".[dev]"
uvicorn mindflow_map.main:app --reload --port 2002

# ── Orchestration Layer (core) ──
cd core
npm install
npm run dev
```

---

## Project Structure

```
monorepo/
├── alphaid/projects/       # Identity Layer (Python FastAPI)
├── nebula/                 # Workflow Engine (Python FastAPI)
├── core/                   # Orchestration Layer (TypeScript)
├── flow/                   # Frontend Portal (Next.js)
├── ghost-main/gateway/     # Unified API Gateway (Python FastAPI)
├── docker-compose.yml      # Development orchestration
├── docker-compose.prod.yml # Production orchestration
├── sql/init/               # Database initialization
├── .github/workflows/      # CI/CD
└── ARCHITECTURE.md         # Architecture design
```

---

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feat/your-feature-name
# or
git checkout -b fix/your-bug-fix
```

### 2. Write Code

Follow existing code style:

- **Python**: `ruff` for lint + format, full type annotations
- **TypeScript**: `eslint` + `prettier`, strict mode
- **Before commit**: `pre-commit run --all-files`

### 3. Write Tests

```bash
# Python modules
pytest tests/ -v --tb=short --cov=src --cov-report=term-missing

# Node.js modules
npm test
```

### 4. Commit

Following Conventional Commits:

```
feat: add user registration API
fix: resolve memory write race condition
docs: update architecture docs
refactor: restructure intent recognition
test: add dual-chain memory tests
chore: update dependencies
```

### 5. Open a PR

- Clear PR title describing the change
- Link related Issues (`Closes #123`)
- All CI checks must pass
- Request code review

---

## Code Standards

### Python

- Type annotations: all function signatures must have types
- Docstrings: public APIs must have docstrings
- Error handling: no empty except blocks, must log
- Async-first: I/O operations must use async/await
- Configuration: no hardcoded values, all via env vars

```python
# ✅ Correct
async def get_user(user_id: str, db: AsyncSession) -> User:
    """Retrieve user by DID. Raises UserNotFound if missing."""
    user = await db.get(User, user_id)
    if not user:
        raise UserNotFound(f"DID {user_id} not registered")
    return user

# ❌ Incorrect
def get_user(user_id):
    user = db.query(user_id)  # no types, no error handling
    return user
```

### TypeScript

- Strict mode (`strict: true`)
- Interfaces preferred over type
- Async functions explicitly return Promise
- No `any` (unless necessary with comment)

```typescript
// ✅ Correct
async function fetchProfile(did: string): Promise<UserProfile> {
  const res = await fetch(`${API_URL}/users/${did}`);
  if (!res.ok) throw new Error(`Failed to fetch profile: ${res.status}`);
  return res.json();
}

// ❌ Incorrect
function fetchProfile(did) {
  return fetch(API_URL + '/users/' + did).then(r => r.json());
}
```

---

## Testing Requirements

| Module | Min Coverage | Test Command |
|--------|-------------|--------------|
| alpha-id | 67% | `pytest tests/ -q --cov=src --cov-fail-under=67` |
| nebula | — | `pytest tests/ -v` |
| core | — | `npm test` |

- New features must include tests
- Bug fixes must include regression tests
- PRs fail if CI coverage drops below threshold

---

## Security Reporting

Found a vulnerability? Please **do not** use public Issues. Instead:

- Email: wenwanqing1217@github.com
- Or GitHub Security Advisory: [Report a vulnerability](https://github.com/wenwanqing1217/monorepo/security/advisories/new)

---

## Code of Conduct

- Be kind, inclusive, and respectful
- Welcome contributors of all levels
- Focus on technology, avoid personal attacks
- Disagree → discuss → reach consensus

---

<p align="center">
  <sub>Thank you to every contributor — Ghost is better because of you.</sub>
</p>
