# MindFlow Autopilot

Autonomous task execution powered by the existing **zcode-brain** agent architecture.

This system lets you say things like:

- `python scripts/autopilot.py "refactor WorkflowEngine"`
- `python scripts/autopilot.py "add rate limiting to wechat API" --dry-run`

...and the system will:
1. Read your existing expert roles from `zcode-brain/roles/*.json`
2. Match the task to the best expert
3. Run safety checks from `zcode-brain/safety/guardrails.json`
4. Decompose the task into subtasks when needed
5. Assemble a validated prompt for execution
6. Run tests
7. Optionally commit and push

## Architecture

```
mindflow-map/autopilot/
├── roles.py         # Reads zcode-brain/roles/*.json
├── safety.py        # Reads zcode-brain/safety/guardrails.json
├── prompt.py        # Assembles system + user prompt
├── orchestrator.py  # Decomposes tasks and assigns roles
├── executor.py      # Generates and applies code changes
├── runner.py        # Task execution scaffold
└── git_workflow.py  # Git automation

scripts/
└── autopilot.py     # CLI entry point
```

## Usage

```bash
# Plan only
python scripts/autopilot.py "refactor WorkflowEngine" --dry-run

# Execute with tests
python scripts/autopilot.py "refactor WorkflowEngine"

# Execute with auto-commit
python scripts/autopilot.py "refactor WorkflowEngine" --auto-commit
```

## Mapping to zcode-brain

| zcode-brain component | autopilot module |
|---|---|
| `dispatcher/role-matcher.ts` | `roles.py` |
| `dispatcher/prompt-assembler.ts` | `prompt.py` |
| `dispatcher/index.ts` | `TaskRunner.plan()` |
| `safety/safety-checker.ts` | `safety.py` |
| `safety/guardrails.json` | reused directly |

## Expert Roles

The autopilot system leverages all roles from `zcode-brain/roles/`, including:
- Backend Architect
- DevOps Engineer
- QA Engineer
- Security Engineer
- Project Manager
- Senior Fullstack Engineer
