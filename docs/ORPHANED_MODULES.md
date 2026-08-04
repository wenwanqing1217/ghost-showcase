<!-- STATUS: REFERENCE -->

# Alpha-ID 孤儿模块说明

> 生成时间: 2026-08-03  
> 范围: `alphaid/projects/src/` 下未被 `entrypoints/` 导入的模块  
> 策略: 保留代码，不删除，记录功能归属

---

## 一、完整孤儿模块清单

### 1. `alpha_id/` 包（60+ 文件）

| 模块 | 大小 | 功能 | 建议 |
|------|------|------|------|
| `agent.py` | 52KB | Alpha-ID Agent 核心逻辑 | 待评估：可能用于 A2A 协议 |
| `ghost_brain.py` | — | GhostBrain 实现 | ⚠️ 已有 `fairy/fairy_brain.py` 替代 |
| `ghost_memory.py` | — | GhostMemory 实现 | ⚠️ 已有 `fairy/fairy_memory.py` 替代 |
| `ghost_character.py` | — | GhostCharacter 实现 | ⚠️ 已有 `fairy/fairy_character.py` 替代 |
| `nuro_bridge.py` | — | NURO 桥接器 | 待评估 |
| `orchestrator.py` | — | 编排器 | 与 `entrypoints/orchestrator.py` 重复？ |
| `tool_orchestrator.py` | — | 工具编排器 | 待评估 |
| `web.py` | — | Web 服务 | 已由 Gateway 替代 |
| `signer.py` | — | 签名工具 | 待评估是否被 auth 使用 |
| `detect.py` | — | 检测工具 | 待评估 |
| `feed.py` | — | Feed 处理 | 待评估 |
| `container.py` | — | 依赖注入容器 | 被 `api/dual_chain.py` 引用 |
| `codex.py` | — | Codex 集成 | 实验性功能 |
| `scene_detection.py` | — | 场景检测 | 被 observer 可能使用 |
| `self_evolution.py` | — | 自进化 | 实验性功能 |
| `poe.py` | — | Poe 集成 | 实验性功能 |
| `__init__.py` | — | 包初始化 | 空文件 |

### 2. `fairy/` 包（8 文件）

| 模块 | 功能 | 状态 |
|------|------|------|
| `fairy_brain.py` | MiniCPM-o 大脑 | ✅ 已由 shim 替代（`alpha_id.ghost_brain`） |
| `fairy_character.py` | 2D 角色渲染 | ✅ 已由 shim 替代（`alpha_id.ghost_character`） |
| `fairy_voice.py` | Whisper + Coqui TTS | ✅ 已由 shim 替代（`alpha_id.ghost_voice`） |
| `fairy_observer.py` | 主动观察循环 | ✅ 已由 shim 替代（`alpha_id.ghost_observer`） |
| `fairy_popup.py` | 气泡通知 | ✅ 已由 shim 替代（`alpha_id.ghost_popup`） |
| `fairy_identity.py` | FOUNDER → DID 派生 | ✅ 已由 shim 替代（`alpha_id.ghost_identity`） |
| `fairy_memory.py` | 双链记忆适配器 | ✅ 已由 shim 替代（`alpha_id.ghost_memory`） |
| `fairy_daily.py` | 每日总结 | ✅ 已由 shim 替代（`alpha_id.ghost_daily`） |

### 3. `mindflow/` 包（8 文件）

| 模块 | 功能 | 状态 |
|------|------|------|
| `engine.py` | 工作流引擎 | 待评估：Flow 微服务已有独立实现 |
| `intent.py` | 意图识别 | 实验性功能 |
| `onboarding.py` | 用户引导 | 实验性功能 |
| `route_optimizer.py` | 路径优化 | 实验性功能 |
| `schedule_parser.py` | 日程解析 | 实验性功能 |
| `agents/` | Agent 定义 | 实验性功能 |

### 4. `core/` 包（35+ 文件，仅 2 个被使用）

| 被使用 | 孤儿 |
|--------|------|
| `http_client.py` | `agent.py` (52KB) |
| `settings.py` | `twin_brain.py` (28KB) |
| | `memory_store.py` (20KB) |
| | `orchestrator.py` |
| | `recovery.py` |
| | `storage_postgres.py` |
| | `dual_chain.py` (被 api/dual_chain.py 引用) |
| | `action_engine/` 目录 |
| | 其他 ~25 个文件 |

### 5. `api/` 包（10 文件，全部孤儿）

| 模块 | 功能 | 建议 |
|------|------|------|
| `a2a.py` | A2A 协议实现 | 待接入：NURO Ghost 或 Gateway |
| `agent.py` | Agent API | 待评估 |
| `dual_chain.py` | 双链记忆 API | 待接入：依赖 `core/dual_chain.py` |
| `gdpr.py` | GDPR 合规 | 待评估 |
| `identity.py` | 身份 API | 待评估 |
| `models.py` | 数据模型 | 被 `dual_chain.py` 引用 |
| `observability.py` | 可观测性 | 待评估 |
| `registration.py` | 注册 API | 待评估 |
| `risk.py` | 风险评估 | 待评估 |
| `social.py` | 社交功能 | 待评估 |

### 6. `auth/` 包（5 文件，全部孤儿）

| 模块 | 功能 | 建议 |
|------|------|------|
| `csrf.py` | CSRF 保护 | 待评估 |
| `jwt.py` | JWT 工具 | 待评估：Gateway 已有 JWT 实现 |
| `middleware.py` | 认证中间件 | 待评估 |
| `token_store.py` | Token 存储 | 待评估 |

### 7. `tools/` 包（部分孤儿）

| 被使用 | 孤儿 |
|--------|------|
| `screen_capture.py` | `ocr.py` |
| `window_control.py` | `security_tool.py` |
| | `tool_decorator.py` |

### 8. 其他孤儿文件

| 文件 | 功能 | 建议 |
|------|------|------|
| `entrypoints/aid_mcp_server.py` | MCP 服务器 (43KB) | 待接入：NURO Ghost 后台服务 |
| `aid_daemon.py` | 守护进程入口 | ✅ 已使用（NURO Ghost 启动） |
| `main.py` | 另一个入口点 | 待评估 |
| `collectors/` (8 文件) | 浏览器/ChatGPT/Claude 采集器 | 实验性功能 |
| `enrichment/` (5 文件) | Doubao 采集 + LLM 丰富 | 实验性功能 |
| `mining/` (3 文件) | 数据挖掘 | 实验性功能 |
| `skills/` (3 文件) | 百度 AI 地图等 | 实验性功能 |
| `profile_schema.py` | 档案 schema | 待评估 |
| `profile_wizard.py` | 档案向导 | 待评估 |
| `repo_cli.py` | Repo CLI | 工具脚本 |
| `scaffold_cli.py` | 脚手架 CLI | 工具脚本 |
| `scaffold_templates.py` | 脚手架模板 | 工具脚本 |

---

## 二、孤儿原因分析

### 2.1 历史原因
- Alpha-ID 最初是作为独立桌面应用开发的（`entrypoints/app.py` 是 50KB 的"上帝类"）
- 随着 Ghost Platform 微服务化，很多功能被拆分为独立服务（Gateway、Nebula、Flow）
- 但原始代码未被清理，导致大量孤儿模块

### 2.2 重构遗留
- `fairy/` 包原本是 NURO Ghost 的核心模块
- 后来通过 shim 模式迁移到 `alpha_id/ghost_*.py`
- 原始 `fairy/` 文件保留了但不再被直接导入

### 2.3 实验性功能
- `collectors/`、`enrichment/`、`mining/`、`skills/` 是数据采集和处理的实验代码
- `mindflow/` 是工作流引擎的早期原型

### 2.4 未来预留
- `api/a2a.py`、`api/dual_chain.py` 等是为未来功能预留的 API 实现
- 当前由 Gateway 代理，但这些模块可能用于独立部署

---

## 三、整合建议

### 3.1 高价值（建议尽快接入）
1. **`api/dual_chain.py` + `core/dual_chain.py`** → 接入 Gateway 或 NURO Ghost 记忆系统
2. **`api/a2a.py`** → 接入 NURO Ghost 的 A2A 协议
3. **`entrypoints/aid_mcp_server.py`** → NURO Ghost 后台 MCP 服务

### 3.2 中价值（可后续评估）
4. **`core/twin_brain.py`** → 双脑架构，可能用于高级 AI 功能
5. **`core/memory_store.py`** → 记忆存储后端
6. **`auth/jwt.py`** → JWT 工具（如果 Gateway 需要独立 JWT 逻辑）

### 3.3 低价值（可归档或删除）
7. **`collectors/`、`enrichment/`、`mining/`** → 实验性数据采集
8. **`skills/`** → 百度 AI 地图等小众功能
9. **`mindflow/`** → 已被 Flow 微服务替代
10. **`fairy/` 原始文件** → 已有 shim 替代

---

## 四、当前状态

- ✅ 所有孤儿模块已**保留**，未删除
- ✅ 已通过 shim 模式保持向后兼容
- ✅ NURO Ghost 入口通过 `feature_flags.py` 统一管理导入
- ⏳ 高价值模块待后续接入
- 📦 低价值模块可考虑归档到 `archive/`

---

*本文档用于记录孤儿模块现状，避免未来重复开发或误删。*
