# Alpha-ID

> Ghost Layer for the AI Era. One identity, every AI tool knows you.

## Quick context

- **Package**: `alpha-id-zix` (v0.3.0), Python 3.12+
- **Project root**: `projects/` — all dev commands run from here
- **Core package**: `projects/src/alpha_id/` (app layer), `projects/src/core/` (core logic)
- **Tests**: `projects/tests/`, pytest

## Before you start (every session)

Read in order — these are the **current entry points** (use today's reality, not old archives):

1. `projects/docs/AGENT_CONTEXT.md` — current phase and constraints
2. `projects/docs/decisions.md` — confirmed decisions
3. `projects/TODO.md` — current execution state

Verify baseline when possible:

```bash
cd projects
python -m pytest tests/test_mining.py -q
```

## Dev setup

```bash
cd projects
pip install -e ".[dev]"
```

## Commands

```bash
python -m pytest tests/test_mining.py -q
ruff check src/
ruff format src/ tests/
python -m pyright src/
```

## Architecture

```
src/
├── alpha_id/          CLI, collectors, mining, web UI, MCP
│   ├── cli.py         main Typer app (entry: aid)
│   ├── collectors/    data importers (chatgpt, claude, cursor, trae, browser)
│   ├── mining/        local trace scanner / extractor / inferrer
│   └── ...
├── core/              core logic (DID, memory, twin brain, agent)
├── api/               FastAPI routes
├── auth/              JWT auth
├── tools/             Desktop automation tools
└── entrypoints/       CLI / MCP / API / Daemon entry points
```

## Current focus

- Keep the full vision: DID / I2I / A2A / dual-brain / simulation disk / MCP injection
- Build the first complete demo path: `aid init → aid profile mine --path . → aid profile show → aid profile web → aid-mcp`
- Improve profile quality: confidence / provenance / completeness / privacy scrubbing

## Hard rules

- Private keys stay client-side, never uploaded
- Do not add orchestration frameworks without explicit user approval
- Do not modify existing tests to make new code pass
- Do not add copyright headers
- Do not touch unrelated code in the same commit
- Use current docs as the source of truth; archive docs are history, not instructions

## Entry points

```bash
aid                     # CLI (Typer)
aid-mcp                 # MCP protocol server
aid-daemon              # Background daemon
aid-api                 # FastAPI REST API
```

## Dev setup

```bash
cd projects
pip install -e ".[dev]"        # core + test + postgres deps
# or: pip install -e ".[all]"  # includes fairy, mcp-server extras
```

## Commands (all via taskipy, run from `projects/`)

```bash
task test              # quick test suite
task test-v            # verbose (full tracebacks)
task test-x            # stop on first failure
task coverage          # tests + coverage report
task lint              # ruff check src/
task format            # ruff format src/ tests/
task typecheck         # pyright src/
task check-all         # format-check + lint + typecheck + test (CI gate)
task dev               # start daemon (aid-daemon)
task web               # start API server with --reload
task dev-mcp           # start MCP server
```

## Architecture

```
src/
├── alpha_id/          CLI, collectors, config, web UI
│   ├── cli.py         main Typer app (entry: aid)
│   ├── collectors/    data importers (chatgpt, claude, cursor, trae, browser)
│   └── ...
├── core/              Zero-external-dep core (DID, memory, twin brain, agent)
├── api/               FastAPI routes
├── auth/              JWT auth
├── tools/             Desktop automation
└── aid_*.py           Entry points (daemon, MCP server, API)
```

Key constraint: **`core/` has zero external dependencies**. No imports from `alpha_id/` into `core/`. Violation breaks the architecture.

## Testing quirks

- `conftest.py` mocks `langchain.tools` — never import real langchain in tests
- Tests auto-redirect `ALPHA_ID_DIR` and `AID_DIR` to `tmp_path` (no real data touched)
- `fairy_agent` and `aid_daemon` tests are excluded from normal `task test` (need API keys / long-running)
- `tests/integration/` requires a live PostgreSQL database
- Coverage threshold: 68% (`pyproject.toml`), CI enforces ≥67%

## CI pipeline (`.github/workflows/ci.yml`)

Runs on push/PR to main: ruff lint → ruff format check → pyright → pytest (ubuntu + windows matrix, Python 3.12)

## Code style (enforced by ruff + pre-commit)

- Double quotes, 4-space indent, 120 char lines
- Ruff rules: E, F, I, N, W, UP, RUF (ignores E501, N999)
- Pre-commit: ruff-format, ruff --fix, mypy, commitizen (commit messages)
- Commit messages follow commitizen convention

## Hard rules

- Private keys stay client-side, never uploaded
- Don't add LangChain, LangGraph, or similar orchestration frameworks
- Don't modify existing tests to make new code pass
- Don't add copyright headers
- Don't touch unrelated code in the same commit
- Check `projects/docs/decisions.md` before any architectural change

## Entry points

```bash
aid                     # CLI (Typer)
aid-mcp                 # MCP protocol server
aid-daemon              # Background daemon
aid-api                 # FastAPI REST API (port 8000)
```

## DB

PostgreSQL via docker-compose (`docker compose up -d`), SQLite fallback for local dev. DB config in `.env` / `.env.example`.
