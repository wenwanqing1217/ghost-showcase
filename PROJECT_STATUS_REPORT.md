# Ghost Platform — 项目状态报告

> **生成时间**: 2026-08-05 | **验证方式**: 亲自执行命令 + 逐行代码阅读
> **重要声明**: 本报告所有结论均基于实际执行结果或代码证据，不写"已验证"除非真的验证过。
> Docker Desktop 在本次验证期间**未运行**，因此所有"服务健康"条目均标注为"未验证"。

---

## 0. 历史问题（2026-08-04 报告造假）

之前的 `PROJECT_STATUS_REPORT.md`（2026-08-04）声称"Docker 全栈已验证 11 服务 healthy"和"800 测试全绿"，经 2026-08-05 实际验证为**虚假声明**：

| 旧报告声称 | 实际情况 |
|:--|:--|
| Docker 全栈已验证 11 服务 ✅ healthy | Docker Desktop 未运行，`docker ps` 报错 `daemon is running: open //./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified`，0 服务在跑 |
| Gateway 53/53 全绿（含 20 e2e） | 默认 pytest collection error 退出（test_proxy.py 顶层 asyncio.run 阻塞）；排除后 32 passed + 20 skipped；e2e 实际只有 14 个不是 20 |
| Alpha-ID 800/702/0/98skip | 实际 901 collected, 802 passed, 1 failed, 98 skipped — 总数/通过数/失败数全错 |
| Flow 3036 ✅ healthy | flow/ 整个目录除 README 被 .gitignore，git clone 后无法构建 |
| Feishu Bot ✅ healthy | feishu-bot 在可选 compose 文件；Dockerfile `COPY bot.py .` 但 bot.py 未被 git 追踪 |
| 凭证安全 | `ghost-main/feishu-bot/.env` 被 git 追踪且含真实 FEISHU_APP_SECRET，3 次提交涉及（含一次"security"提交） |

---

## 1. 服务健康状态

**所有服务均未通过 Docker 验证**（Docker Desktop 未运行）。下表为代码入口审查结论：

| 服务 | 端口 | 验证状态 | 入口审查结论 |
|:-----|-----:|:---------|:-------------|
| Gateway | 18080 | ❓ 未验证 | [app.py](file:///d:/MW/ghost-main/gateway/app.py) 入口完整；[server.mjs](file:///d:/MW/ghost-main/gateway/server.mjs) fallback 已修端口（P1-4） |
| Alpha-ID | 8000 | ❓ 未验证 | [entrypoints/api.py](file:///d:/MW/alphaid/projects/src/entrypoints/api.py) 入口存在；`from src.main import app` 路径脆弱 |
| Nebula | 2002 | ❓ 未验证 | [main.py](file:///d:/MW/nebula/src/mindflow_map/main.py) lifespan + WorkflowEngine 完整 |
| Ghost DS | 3001→3000 | ❓ 未验证 | [layout.tsx](file:///d:/MW/DS/src/app/layout.tsx) + Next.js 入口完整；端口 3001:3000 映射 |
| Orchestrator | 19090 | ❓ 未验证 | [main.py](file:///d:/MW/orchestrator/main.py) 入口完整；但 OrchestratorEngine 启动后未注册任何 channel/loop |
| ToolA | 8081 | ❓ 未验证 | [main.py](file:///d:/MW/tool-a/main.py) 无 OPENAI_API_KEY 时返回 stub |
| ToolB | 8082 | ❓ 未验证 | 同上 |
| Feishu Bot | — | ❓ 未验证 | [Dockerfile](file:///d:/MW/ghost-main/feishu-bot/Dockerfile) `COPY bot.py` 但 bot.py 未被 git 追踪 |
| Net-Agent | 18180 | ❓ 未验证 | [main.py](file:///d:/MW/ghost-main/net_agent_server/main.py) 入口存在 |
| Flow | 3036 | ❓ 未验证 | [flow/](file:///d:/MW/flow) 源码已纳入 git（P0-3 修复） |
| Redis | 6379 | ❓ 未验证 | docker-compose.yml 定义完整 |

## 2. 测试覆盖状态（亲自执行结果）

| 项目 | 实际执行结果 | 备注 |
|:-----|:------------|:-----|
| Gateway | `32 passed, 20 skipped` ✅ | test_proxy.py 修复后（P1-1），收集正常；20 skipped 是缺服务的 skip |
| Orchestrator | `7 passed` ✅ | engine.py 改动后（P1-5）仍全绿 |
| Nebula | `153 passed` ✅ | 历史声称属实 |
| Alpha-ID 核心 | `802 passed, 1 failed, 98 skipped` ⚠️ | 1 failed 是沙箱权限问题（`PermissionError` 访问 `~/.alpha-id/alpha_id.db-wal`），非代码 bug；98 skipped 多数因缺 FastAPI/Tesseract 环境 |
| Alpha-ID 全量（本轮） | `859 passed, 0 failed, 98 skipped` ✅ | 修复 4 个失败：3 个 `asyncio.get_event_loop()` Python 3.12 兼容（测试代码）、1 个沙箱权限（测试改用 monkeypatch Path.home 隔离数据目录）；2 个坏测试补 await |
| Alpha-ID lint（本轮） | `ruff 0 errors` ✅ | 全量清理：F401/F811/E402/F841/E741/N806/N803/N812/N818/W293/W291；真实 bug 修复：alpha_social.get_friends 重复定义、feature_flags 顶层无条件导入破坏降级、smart_capture/ghost_character 死代码 |
| DS（本轮） | `tsc 0 errors + vitest 45 passed + next build exit 0` ✅ | 构建链路首次全绿；修复 #13-#23 真实 bug（见第 6 节） |
| DS 本地冒烟（本轮） | `/api/stats` 200 真实种子数据 + `/dashboard` 200 ✅ | SQLite 本地模式播种 5 商品 + 6 订单，看板非空可演示 |
| Alpha-ID 新模块 | `79 passed` ✅ | agent_graph / alpha_social / diy_cli / tenant_panel / credits_growth / critical_bugfixes 6 个测试文件（2026-08-05 新增补测） |
| DS | `45 passed (3 test files)` ✅ | 历史报告说"无后端单测"过时；含 eventbus-init 测试 |
| flow（会话 4 新增） | `30 passed (7 test files)` ✅ | workspace 依赖 `workspace:*` → `file:` 修复后，npm test 全绿 |
| net-agent（Session 15 新增） | `12 passed (3 test files)` ✅ | 从"测试目录为空（CI exit 5）"补测至 12 passed；修出循环导入/`async with` 缺失等 4 个真实 bug |
| **全仓合计（会话 15）** | **1138 passed** ✅ | alphaid 859 + nebula 153 + gateway 32 + orchestrator 7 + net-agent 12 + DS 45 + flow 30；ruff 全绿；详见 [DATA_FLOW.md](DATA_FLOW.md) |

## 3. P0 阶段修复（2026-08-05）

1. **凭证泄露处理** — `ghost-main/feishu-bot/.env` 从 git 追踪移除（`git rm --cached`，本地文件保留）；创建 [.env.example](file:///d:/MW/ghost-main/feishu-bot/.env.example) 模板；[docker-compose.feishu.yml](file:///d:/MW/docker-compose.feishu.yml) 移除 env_file 引用，改为从主 .env 通过 environment 注入
2. **docker-compose.override.yml ghost-net external 错误** — 删除 `networks: ghost-net: external: true`，prometheus/grafana 改用默认网络
3. **flow/ 源码纳入 git** — 移除 .gitignore 中 `flow/` + `!flow/README.md`，24 文件 1420 行已 staged

## 4. P1 阶段修复（2026-08-05）

4. **test_proxy.py 顶层 asyncio.run 阻塞收集** — 包入 `if __name__ == "__main__":`；`async def test()` 重命名为 `run_smoke_test()`（避免被 pytest 当测试函数收集）；ALPHAID_URL 从硬编码 8002 改为 env 变量+默认 8000
5. **tool_orchestrator.py:342 NameError** — `if not orch.execute(task):` 改为 `if not orch.execute(task_id):`（task_id 是函数参数，task 未定义）
6. **server.mjs 错端口 8002 + 硬编码端口** — ALPHAID_URL/NEBULA_URL/GATEWAY_PORT 全部改为 env 变量+默认值；8002 修正为 8000
7. **engine.py write_note/send_feishu 空实现** — 通过 EventBus emit MEMORY_WRITTEN/SOCIAL_MESSAGE 事件，返回真实 note_id/True；不再返回空字符串/False

## 5. P2/P3 阶段修复（2026-08-05 盘活）

8. **DS 登录认证绕过（原#2）** — 修复 login 页 catch 块直接放行；新增 `/api/v1/human/identity` 真实身份查询；Sidebar 加登录/登出入口（D-20260805-03）
9. **ProductAiDialog 保存 bug（原#3）** — `handleSave` 改用 `result.description`（AI 优化后文案）入库
10. **lib/api.ts 15+ 死方法（原#4）** — 清理 agent/flow/internal/net 死客户端层；新增真实 API 客户端（channel-copy/growth/credits/agent-market）
11. **Layout 强制 Sidebar（原#5）** — login/demo/首页独立布局，不再被 Sidebar 破坏
12. **brain 硬编码 Alpha-001（原#6）** — 从 JWT 读取真实 alpha_id，多租户身份隔离
13. **A2A 页面假数据（原#7）** — 移除 `Math.random()*20+80`，改调真实 `/api/v1/agent/a2a/market`；新增 agent-market / my-agents 页 + `/api/v1/credits` 钱包
14. **webhook shoplazza→onebound 重命名（原#8）** — 目录与内容一致；补 route.test.ts
15. **OrchestratorEngine 空转（原#9）** — 注册 GatewayChannelAdapter + gateway_sync_loop 数据循环；`/health` 端点返回真实 stats（9e763a6）
16. **mindflow 包孤岛（原#10）** — 补 `__init__.py` + `api/mindflow.py` 端点 + main.py 注册路由；修复 intent.py `_llm_classify` 未定义 bug；Gateway routes/human.py 新增 mindflow 代理路由（9e763a6）
17. **workflow 页面 API 路径不匹配（原#11）** — 修正为真实路由，工作流真链路（不再 demo 数据）
18. **settings 店铺模式切换假成功（原#12）** — 修正 API 调用 + TenantMapping 多租户映射（D-20260805-04）
19. **DS 内容生成闭环** — 新增 `/content` 创建表单（视频/游戏生成）+ `/api/content/generate` 代理路由（D-20260805-01/02）；Gateway 新增 `/v1/content/*`（video/game proxy）
20. **飞书指令中心（Nebula）** — 新增 `feishu_commands.py` 指令路由器（文案/视频/抖音/短剧/帮助），复用 DS/Gateway/nebula 已有能力；feishu_webhook 优先指令路由，未识别才走 AI 闲聊
21. **渠道助手页（DS）** — 新增 `/channels` 页面 + `/api/ai/channel-copy` 端点：输入商品/卖点/价格/成色 → 一键生成闲鱼+小红书文案，可续生成种草视频并发布 TikTok/YouTube（0 成本闭环：小红书种草引流 → 闲鱼成交 / TikTok 出海）
22. **Growth 追踪器** — 新增 `growth_tracker.py`（监听 GROWTH_EVENT 累计成长值，6 阶段精灵进化）+ `/growth` 页面 + `/api/growth/*`
23. **NURO 反向通道（Gateway）** — 新增 `/v1/nuro/*`：WebSocket 云端→本地桌宠推送桥（提醒/进化/指令结果）
24. **GameEngine（Gateway）** — 新增 `services/game_engine.py`：模板化 HTML5 游戏生成器（5 种类型 × 5 种主题）
25. **doubao 遗留清理** — 删除 ghost-capture/、doubao_reader/、doubao-bridge 全部死代码（并入 GHOST.md 已移除豆包线）

## 6. 已知未修复问题（按严重度排序）

### 🚨 致命 — 必须立即处理

| # | 问题 | 文件 | 说明 |
|:--|:-----|:-----|:-----|
| 1 | 飞书 App Secret 已进 git 历史 | [feishu-bot/.env:3-4](file:///d:/MW/ghost-main/feishu-bot/.env#L3-L4) | P0-1 移除了工作区追踪，但 cde0528/91ea228/f0c0811 三次提交历史仍含真实凭证。**用户必须去飞书开放平台轮换 App Secret**，然后用 git filter-repo 清理历史 |

### ⚠️ 严重 — 应尽快处理

| # | 问题 | 文件 |
|:--|:-----|:-----|
| 2 | 全栈未 Docker 验证（Docker Desktop 未运行） | 需 `make up` + `make test` 实测 11 服务健康 |
| 3 | 基建自替换 benchmark 依赖真实调用数据积累 | agent_graph.record_call 已接真数据，但冷启动无历史时评分同分不替换 |

已解决（2026-08-05 质量加固）：
- ~~#13 demo 调不存在的 generate-did API~~ — demo 页改为纯前端模拟（[demo/page.tsx](file:///d:/MW/DS/src/app/demo/page.tsx#L26)），不再发 404 请求，真实注册走 /register
- ~~#14 demo 跳 /app/register~~ — 已改跳真实 /register 路由（上轮修复）
- ~~#15 obsidian URL 拼接缺 `?`~~ — filter=all 时 `cards&limit=50` 修正为 `cards?limit=50`（[obsidian/page.tsx:82](file:///d:/MW/DS/src/app/ecosystem/obsidian/page.tsx#L82)）
- ~~#16 obsidian updated_at 属性不存在~~ — Card 接口已加 `updated_at?`（上轮修复）
- ~~#17 RevenueChart `var(--text)` 不存在~~ — 改为 `var(--text-primary)`（[RevenueChart.tsx:104](file:///d:/MW/DS/src/components/RevenueChart.tsx#L104)）
- ~~#18 demo 订单状态值与 StatusBadge 不匹配~~ — processing→paid、shipped/delivered→fulfilled（[demo-data.ts](file:///d:/MW/DS/src/lib/demo-data.ts)）
- ~~#19 chat 离线模式固定话术~~ — 回复引用用户输入，更自然（[chat/page.tsx:174](file:///d:/MW/DS/src/app/chat/page.tsx#L174)）
- ~~#20 AuthGuard 鉴权过松~~ — 200 时校验响应含真实身份字段（alpha_id/did/id），防止异常 200 空数据绕过（[AuthGuard.tsx:23](file:///d:/MW/DS/src/components/layout/AuthGuard.tsx#L23)）
- ~~#22 端口三处不一致~~ — package.json dev 3004→3000，与 AGENTS.md/compose 统一
- ~~#23 feishu-bot Dockerfile COPY 未追踪文件~~ — bot.py/requirements.txt/feishu_service.py 强制纳入 git（根 .gitignore 放行 + git add -f），镜像可构建

已解决（上轮）：~~#22 无 error boundary~~（新增 error.tsx）、~~#24 内容详情页~~（/content 已加创建表单）

## 7. 下一步行动

**已完成**：P0（凭证移除/网络/flow 入库）、P1（9 个 DS 致命 bug）、P2（调度层免费优先 + 每日最优自替换 + 飞书社交 + DIY CLI + 多租户面板）、P3（AgentGraph/alpha_social/diy_cli/tenant_panel 补测 64 passed；DIY adapter + 外部 skill 市场 + 6 业务意图落地；渠道助手 + 飞书指令中心 + 内容生成闭环）、**质量加固（上轮）**：ruff 全绿 + alphaid 859 测试全绿 + DS 构建链路全绿（tsc/vitest/build）+ #13-#23 真实 bug 修复 + 种子数据 + 本地冒烟通过、**lint 硬化（Session 15）**：统一 ruff 配置全绿 + net-agent 测试 0→12 + 修出循环导入/async with/str+bytes/F821 等 10+ 真实 bug + SYSTEM_MAP/PROJECT_MAP 文档补全 + 全仓 1138 测试连过

**待办（按优先级）**：
1. **用户操作**：去飞书开放平台轮换 App Secret（历史提交含凭证，必须轮换）
2. **Docker 全栈验证**：启动 Docker Desktop → `make up` → `make test`，实测 11 服务健康（当前代码级已验证，容器级未验）
3. **打包分发**：按 docs/planning/PACKAGING_STRATEGY.md 完成安全审查 → 补测 → 打包（Trae 式可下载客户端）
4. **#21 catch 静默吞错误**：obsidian/social 页面 catch 块补用户可见错误提示，随版本迭代清理

**用户必须操作**：
1. 去飞书开放平台 https://open.feishu.cn/app 轮换 `cli_aad59b68b879dbe7` 的 App Secret
2. （可选）安装 git filter-repo 后运行 `git filter-repo --path ghost-main/feishu-bot/.env --invert-paths` 清理历史
3. 启动 Docker Desktop 后才能验证服务健康状态

---

## 8. Session 12/13 新增模块（2026-08-05，已测试）

| 模块 | 文件 | 状态 | 说明 |
|:-----|:-----|:----:|:-----|
| 调度层免费优先 | `core/agent_graph.py` find_best_agent | ✅ 已测试 | 4层tier排序：基建→自己→好友→其他免费；付费仅兜底 |
| 基建自替换 | `core/agent_graph.py` benchmark_skill/swap_to_best + `orchestrator/engine.py` _optimal_swap_loop | ✅ 已测试 | **每日**巡检（86400s）；≥5分增益才替换；真实调用统计评分；EventBus广播 |
| 飞书社交 | `core/alpha_social.py` UserBinding/sync_feishu_contacts + `api/social.py` 3端点 + `container.py` 双向注入 | ✅ 已测试 | 绑定alpha_id↔飞书；拉通讯录自动加好友 |
| DIY CLI | `alpha_id/diy_cli.py` + `cli.py` aid chat入口 | ✅ 已测试 | 16 种意图（9 基础 + 6 业务场景 + codex adapter）；LLM+本地双解析；chat/repl/intents |
| 多租户面板 | `api/tenant_panel.py` /u/{alpha_id}/dashboard | ✅ 已测试 | 8tab独立面板；工作台CRUD；iframe嵌入；多租户隔离 |
| 外部 skill 市场 | `core/agent_graph.py` register_external_source/sync_external_skills | ✅ 已测试 | OpenRouter/Gorilla/自建源注册；幂等同步；external agent 参与选路 |
| 积分钱包 | `core/credits.py` + `api/credits.py` | ✅ 已测试 | 新用户 100 积分；交易流水；退款；10% 平台费；4 条计费规则 |
| A2A 市场 | `api/a2a.py`（+560 行） | ✅ 已测试 | Ed25519/API Key 双注册；approved/pending/delisted 状态机；market 搜索 |
| 总助调度 | `api/agent_dispatch.py` /api/v1/agent/dispatch | ✅ 已测试 | 意图→findskill→调用→record_call 闭环；内部 growth_stats 分支 |
| 成长追踪 | `alpha_id/growth_tracker.py` | ✅ 已测试 | 6 阶段精灵进化；GROWTH_EVENT 累计；内存缓存自持 |

**验证状态**: `79 passed`（6 个测试文件，2026-08-05 亲自执行）。Docker 全栈验证仍待用户启动 Docker Desktop。

---

## 9. Session 14 — 2026-08-05（CI 可跑 + 数据流可读 + 仓库专业化）

### 背景
用户反馈：平台"数据怎么流看不清、没串联、推到 GitHub 不专业、自动化编程不好做"。本轮解决三件事：**CI 真能跑、数据流讲得清、README 像样**。

### 1. CI 修复（GitHub Actions 真能过）
| 问题 | 修复 |
|:-----|:-----|
| gateway/orchestrator 无 pyproject.toml，`pip install -e ".[dev]"` 必挂 | [reusable-python-ci.yml](.github/workflows/reusable-python-ci.yml)：按文件存在性分流（pyproject → `.[dev]`；requirements.txt → `-r` + pytest/ruff） |
| e2e 任务缺 `DB_PASSWORD`（compose 强校验），`docker compose up` 必挂 | [ci.yml](.github/workflows/ci.yml)：e2e job 补 env；显式列出 10 个服务，**跳过 MoneyPrinterTurbo**（仓库不含该目录） |
| e2e 触发条件只认 3 个服务 | 扩为 6 个 Python 服务任一成功即触发 |
| DS health 脚本端口 3004 错 | 修正为 3000（[DS/package.json](DS/package.json)） |
| flow `workspace:*` 协议 npm 不支持（本地 + CI 都会挂） | [flow/apps/api/package.json](flow/apps/api/package.json) 改用 npm 原生 `file:../../packages/shared` |

### 2. 新增 DATA_FLOW.md（数据怎么流）
- 6 条业务闭环（A 飞书指令→内容 / B 看板↔网关↔身份 / C OneBound Webhook / D A2A 市场+信用 / E 工作流执行 / F 调度换优）
- 每条闭环：真实端点路径 + 涉及文件 + 验证状态（✅ 单测 / ⚠️ 需 Docker e2e / ❌ 未落地）
- **诚实未落地清单**：飞书真实收发、MoneyPrinterTurbo 视频、闲鱼/小红书自动发布、OPTIMAL_SWAP 运行态

### 3. README 重写 + Makefile smoke
- README：删两套冲突快速启动、删旧路径 `alpha_id/`、删"11/12 服务运行中"虚假声明；改为 badges + 架构图 + 单条快速启动 + 实测测试表 + 真实状态（含未落地清单）；修复 2 个断链（SYSTEM_MAP/PROJECT_MAP 不存在）
- Makefile：新增 `make smoke`（6 子项目一键全量单测，无 Docker），`make test` 改指 smoke；去掉 `2>/dev/null || echo` 掩盖失败的问题

### 4. 本地实测（无 Docker 可跑的全部）
- alphaid 859 ✅ / nebula 153 ✅ / gateway 32 ✅ / orchestrator 7 ✅ / DS 45 ✅ / flow 30 ✅ = **1126 passed**
- flow 依赖修复后 `npm test` 全绿（此前 `workspace:*` 导致无法安装）

### 待办不变
- 用户轮换飞书 App Secret；启动 Docker Desktop 跑 `make up` + `node scripts/e2e_test.mjs --wait`

---

## 10. Session 15 — 2026-08-05（lint 硬化 + 真实 bug 修复 + net-agent 补测）

**背景:** 承接 Session 14 继续推进，把"CI 能跑"落到"本地 lint 全绿 + 全仓测试连过"，并补齐 net-agent 测试空白。

### 成果
1. **ruff 全绿** — 统一 ruff 配置（ghost-main/gateway/orchestrator 新建 ruff.toml + nebula pyproject.toml），中文注释豁免 RUF001/2/3，全仓 lint 0 errors
2. **10+ 真实 bug 修复**（lint 揪出，非格式）：
   - F821 未定义名：nebula `supply.py` 缺 `datetime` 导入、`supply/base.py` `_global_supply_registry` 未定义、gateway `internal.py` `EventType.SOCIAL_MESSAGE` 不存在 — 均为运行时必炸
   - gateway `tenant.py` `str += bytes` TypeError（JWT 未对齐即炸）+ N806 大写常量规范
   - net-agent：vendor_registry 循环导入（改 `importlib` 惰性加载 + 恢复误删的 `list_vendors()`）；`adapters/base.py` `async with` 从未实现（`@asynccontextmanager` 误装饰 `__aenter__`，重写手写协议）
3. **net-agent 测试 0 → 12** — 新建 conftest.py（env + sys.path）+ test_auth.py + test_adapters.py；补 requirements（cryptography/python-jose）；新建 ghost-main/requirements.txt 供 CI 安装
4. **构建/CI 硬化** — compose MoneyPrinterTurbo 改 `profiles: ["media"]` 可选；.gitignore 移除全局 package.json 忽略（flow/gateway 清单入库根因）；flow map.ts TS 类型收窄修复
5. **文档 L1-L4 齐备** — 新建 SYSTEM_MAP.md（L3）/ PROJECT_MAP.md（L4）；GHOST.md 核心文档表补入；README/DATA_FLOW 同步 1138

### 验证
- 全仓 **1138 passed**：alphaid 859 / nebula 153 / gateway 32 / orchestrator 7 / net-agent 12 / DS 45 / flow 30，ruff 全绿（2026-08-05 亲自执行）

### 待办不变
- 用户轮换飞书 App Secret；启动 Docker Desktop 跑全栈 E2E；打包分发按 PACKAGING_STRATEGY.md 前置条件推进
