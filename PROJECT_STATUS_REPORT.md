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
| Alpha-ID | `802 passed, 1 failed, 98 skipped` ⚠️ | 1 failed 是沙箱权限问题（`PermissionError` 访问 `~/.alpha-id/alpha_id.db-wal`），非代码 bug；98 skipped 多数因缺 FastAPI/Tesseract 环境 |
| DS | `45 passed (3 test files)` ✅ | 历史报告说"无后端单测"过时 |

## 3. P0 阶段修复（2026-08-05）

1. **凭证泄露处理** — `ghost-main/feishu-bot/.env` 从 git 追踪移除（`git rm --cached`，本地文件保留）；创建 [.env.example](file:///d:/MW/ghost-main/feishu-bot/.env.example) 模板；[docker-compose.feishu.yml](file:///d:/MW/docker-compose.feishu.yml) 移除 env_file 引用，改为从主 .env 通过 environment 注入
2. **docker-compose.override.yml ghost-net external 错误** — 删除 `networks: ghost-net: external: true`，prometheus/grafana 改用默认网络
3. **flow/ 源码纳入 git** — 移除 .gitignore 中 `flow/` + `!flow/README.md`，24 文件 1420 行已 staged

## 4. P1 阶段修复（2026-08-05）

4. **test_proxy.py 顶层 asyncio.run 阻塞收集** — 包入 `if __name__ == "__main__":`；`async def test()` 重命名为 `run_smoke_test()`（避免被 pytest 当测试函数收集）；ALPHAID_URL 从硬编码 8002 改为 env 变量+默认 8000
5. **tool_orchestrator.py:342 NameError** — `if not orch.execute(task):` 改为 `if not orch.execute(task_id):`（task_id 是函数参数，task 未定义）
6. **server.mjs 错端口 8002 + 硬编码端口** — ALPHAID_URL/NEBULA_URL/GATEWAY_PORT 全部改为 env 变量+默认值；8002 修正为 8000
7. **engine.py write_note/send_feishu 空实现** — 通过 EventBus emit MEMORY_WRITTEN/SOCIAL_MESSAGE 事件，返回真实 note_id/True；不再返回空字符串/False

## 5. 已知未修复问题（按严重度排序）

### 🚨 致命 — 必须立即处理

| # | 问题 | 文件 | 说明 |
|:--|:-----|:-----|:-----|
| 1 | 飞书 App Secret 已进 git 历史 | [feishu-bot/.env:3-4](file:///d:/MW/ghost-main/feishu-bot/.env#L3-L4) | P0-1 移除了工作区追踪，但 cde0528/91ea228/f0c0811 三次提交历史仍含真实凭证。**用户必须去飞书开放平台轮换 App Secret**，然后用 git filter-repo 清理历史 |
| 2 | DS 登录认证绕过 | [login/page.tsx:40,55-57](file:///d:/MW/DS/src/app/login/page.tsx#L40) | 调用不存在的 quick-register API → catch 块直接 `router.push('/chat')`，任何人点登录都能进系统 |
| 3 | ProductAiDialog 保存 bug | [ProductAiDialog.tsx:108](file:///d:/MW/DS/src/components/ProductAiDialog.tsx#L108) | `handleSave` 发送 `product.description`（原始）而非 `result.description`（AI 优化后），用户付费 AI 优化但数据库存的是旧文案 |
| 4 | lib/api.ts 15+ 死方法指向不存在端点 | [lib/api.ts:104-212](file:///d:/MW/DS/src/lib/api.ts#L104) | agent/flow/internal/net 客户端层全部死代码 |
| 5 | Layout 在 login/demo/首页强制渲染 Sidebar | [layout.tsx:30](file:///d:/MW/DS/src/app/layout.tsx#L30) | 登录页/落地页布局被破坏 |
| 6 | brain 页面硬编码 Alpha-001 | [brain/page.tsx:65,89](file:///d:/MW/DS/src/app/brain/page.tsx#L65) | 所有用户操作同一大脑，无身份隔离 |
| 7 | A2A 页面调用不存在的 API + 伪造 success_rate | [ecosystem/a2a/page.tsx:54-55,70](file:///d:/MW/DS/src/app/ecosystem/a2a/page.tsx#L70) | `Math.random() * 20 + 80` 生成假数据 |
| 8 | webhook/shoplazza 文件名 vs 内容不一致 | [api/webhook/shoplazza/route.ts](file:///d:/MW/DS/src/app/api/webhook/shoplazza/route.ts) | 文件名是 shoplazza 但代码处理 OneBound |
| 9 | OrchestratorEngine 启动但未注册任何渠道/循环 | [orchestrator/main.py:186-188](file:///d:/MW/orchestrator/main.py#L186-L188) | L4 调度层完全空转 |
| 10 | mindflow/ 整个包完全孤岛 | [alphaid/projects/src/mindflow/](file:///d:/MW/alphaid/projects/src/mindflow) | 无任何外部 import |
| 11 | workflow 页面 API 路径与实际路由不匹配 | [workflow/page.tsx:43,73,92](file:///d:/MW/DS/src/app/workflow/page.tsx#L43) | 工作流永远走 demo 数据 |
| 12 | settings 页面店铺模式切换 API 不存在但 UI 乐观更新 | [settings/page.tsx:100](file:///d:/MW/DS/src/app/settings/page.tsx#L100) | 用户以为切换成功，实际未生效 |

### ⚠️ 严重 — 应尽快处理

| # | 问题 | 文件 |
|:--|:-----|:-----|
| 13 | demo/page.tsx 调用不存在的 generate-did API | [demo/page.tsx:33](file:///d:/MW/DS/src/app/demo/page.tsx#L33) |
| 14 | demo/page.tsx 跳转到不存在的 /app/register 路由 | [demo/page.tsx:243](file:///d:/MW/DS/src/app/demo/page.tsx#L243) |
| 15 | obsidian 页面 URL 拼接错误（缺 `?`） | [ecosystem/obsidian/page.tsx:82](file:///d:/MW/DS/src/app/ecosystem/obsidian/page.tsx#L82) |
| 16 | obsidian 页面访问不存在的 updated_at 属性 | [ecosystem/obsidian/page.tsx:338](file:///d:/MW/DS/src/app/ecosystem/obsidian/page.tsx#L338) |
| 17 | RevenueChart 使用不存在的 CSS 变量 --text | [RevenueChart.tsx:104](file:///d:/MW/DS/src/components/RevenueChart.tsx#L104) |
| 18 | demo 订单状态值与 StatusBadge 不匹配 | [demo-data.ts:84-126](file:///d:/MW/DS/src/lib/demo-data.ts#L84) vs [StatusBadge.tsx:8-17](file:///d:/MW/DS/src/components/StatusBadge.tsx#L8) |
| 19 | chat 离线模式固定话术 | [chat/page.tsx:178-183](file:///d:/MW/DS/src/app/chat/page.tsx#L178) |
| 20 | AuthGuard 鉴权过松（只检查 res.ok） | [AuthGuard.tsx:23-28](file:///d:/MW/DS/src/components/layout/AuthGuard.tsx#L23) |
| 21 | 多处 catch 静默吞错误 | obsidian/page.tsx:74,103; social/page.tsx:71 |
| 22 | 无 error boundary（运行时错误白屏） | DS/src/app/ 下无 error.tsx |
| 23 | 端口三处不一致 | package.json:7 (3004) vs AGENTS.md (3000) vs compose (3001:3000) |
| 24 | 内容详情页 + 编辑/删除待实现 | DS/src/app/content/ |
| 25 | feishu-bot Dockerfile COPY 未追踪的 bot.py | [feishu-bot/Dockerfile:43](file:///d:/MW/ghost-main/feishu-bot/Dockerfile#L43) |

## 6. 下一步行动

**P2 阶段（DS 真功能闭环）** — 修第 5 节 #2-#8、#11-#12 共 9 个 DS 致命 bug，让电商看板真的能用

**P3 阶段（架构盘活）** — 修第 5 节 #9-#10，让 OrchestratorEngine 真工作，接通 mindflow 包

**用户必须操作**：
1. 去飞书开放平台 https://open.feishu.cn/app 轮换 `cli_aad59b68b879dbe7` 的 App Secret
2. （可选）安装 git filter-repo 后运行 `git filter-repo --path ghost-main/feishu-bot/.env --invert-paths` 清理历史
3. 启动 Docker Desktop 后才能验证服务健康状态
