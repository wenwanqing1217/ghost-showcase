# Ghost Platform 交接文档（HANDOFF）

> **给新模型：读这一个文件就能进入状态。最后更新：2026-08-05**
> **必读顺序：本文件 → GHOST.md（七层架构+已知问题）→ PROJECT_STATUS_REPORT.md（25个bug清单）→ AGENTS.md（术语+禁止事项）**

---

## 一、项目是什么

Web4.0 AtoA（Agent-to-Anything）全域自主智能体操作系统。三层堆栈：
- **理念层**：Denny AI（人机共生哲学）
- **系统中枢**：Alpha-ID（DID 身份 + 双链记忆 + AgentLoop）
- **底层网络**：Ghost AtoA（统一网关 + 事件总线 + 服务编排）

七层架构：L1感知(飞书/Web/NURO/CLI) → L2身份(Alpha-ID:8000) → L3工作流(Nebula:2002) → L4调度(Orchestrator:19090) → L5网关(Gateway:18080) → L6业务(Ghost DS:3001) → L7知识(MemoryGraph/Obsidian)

---

## 二、项目里已有的业务场景（重要！别漏了）

项目**不是空壳**，已有完整的电商内容生成闭环：

| 场景 | 实现位置 | 状态 |
|:--|:--|:--|
| **闲鱼+小红书文案** | DS `channels/page.tsx` + Nebula `ChannelCopyTool` + Alpha-ID `agent_dispatch._call_ds_copy` | ✅ 后端完整 |
| **抖音短剧发布** | Nebula `automation/douyin.py`(Playwright) + `ShortDramasPrecheckTool` + `script_generator.py` | ✅ 后端完整 |
| **短视频生成** | MoneyPrinterTurbo + Gateway `routes/content.py` + DS content 页 | ✅ 后端完整 |
| **跨平台发布** | Gateway `/v1/content/video/publish`（TikTok/YouTube/Instagram） | ✅ 后端完整 |
| **HTML5游戏生成** | Gateway `services/game_engine.py`（5类型×5主题）+ DS content 页 | ✅ 后端完整 |
| **商品AI文案** | DS `lib/ai.ts` + `ProductAiDialog` + `/api/ai/copy` | ✅ 后端完整 |
| **直播** | 无 | ❌ 完全没做 |

**Nebula 8个内置工具**：`douyin`/`shortdramas`/`channel_copy`/`video_generate`/`video_publish`/`shopify`/`map`/`chat`（见 `nebula/src/mindflow_map/workflows/engine.py` L381-394）

**AgentGraph 调度的 agent**：`tool:ds-copy`(文案)、`tool:moneyprinter`(视频)、`core:alpha-id`(内部)、`feed`(资讯)（见 `alphaid/projects/src/api/agent_dispatch.py` L100-114）

**成长值奖励映射**：`channel_copy:2, video_generate:3, video_publish:5, douyin:4, shortdramas:3, map:1, shopify:3`（见 `growth_tracker.py` L49-57）

---

## 三、本次会话（Session 12）做了什么

### 已完成的 4 个模块（代码完成，未测试）

| 模块 | 文件 | 关键改动 |
|:--|:--|:--|
| **调度层免费优先** | `core/agent_graph.py` find_best_agent | 4层tier排序：基建(0)→自己(1)→好友(2)→其他免费(3)；付费仅兜底；`_preferred`让基建自替换立即生效 |
| **基建自替换** | `core/agent_graph.py` benchmark_skill/swap_to_best/run_optimal_swap_pass + `orchestrator/engine.py` _optimal_swap_loop | 按 免费×40+成功率×40+延迟×20 评分；≥5分增益才替换；每小时巡检(需改成每天)；EventBus广播 |
| **飞书社交** | `core/alpha_social.py` UserBinding/sync_feishu_contacts + `api/social.py` 3端点 + `container.py` 双向注入 | 绑定alpha_id↔飞书；拉通讯录自动加好友；`_ensure_friendship`双向写 |
| **DIY+多租户面板** | `alpha_id/diy_cli.py` + `cli.py` aid chat + `api/tenant_panel.py` + `main.py` | 9种意图LLM+本地双解析；`/u/{alpha_id}/dashboard` 8tab面板；工作台CRUD；iframe嵌入 |

### 探讨过但需要修正的 5 个点（用户已确认方向，未实现）

| # | 修正点 | 用户原话/意图 | 该怎么做 |
|:-:|:--|:--|:--|
| 1 | **DIY CLI 改成 adapter 层** | "cli接codex或者一些比较火的是不是方便一点" | 不自造意图解析，改成转发给 Codex/Claude/Aider（用户自选），我们只负责执行+注册到Alpha-ID |
| 2 | **基建自替换频率降低** | "基建我们本来选的就是最好的，更新没这么快" | 从每小时(3600s)改成每天(86400s)凌晨跑；连续3天低于候选才替换 |
| 3 | **benchmark用真实数据** | "每天根据咨询就能内部打榜" | 接EventBus真实调用事件(成功率/调用量/延迟/用户反馈)，不用占位`_success_rate` |
| 4 | **接外部skill市场** | "也有现成的找最好的最优的一些skill" | AgentGraph加外部路由源(OpenRouter/Gorilla等)，内部没有时自动查外部市场 |
| 5 | **补全业务场景意图** | "你的输出那些小红书咸鱼游戏啥的全漏了" | DIY CLI+面板补7个意图：channel_copy/douyin/shortdramas/video_generate/video_publish/game/product_copy |

### 代码已更新但文档未更新的部分

以下文档已同步更新：WORK_LOG.md（Session 12）、DECISIONS.md（D-06~D-09）、GHOST.md（仍待修复表+术语表）、PROJECT_STATUS_REPORT.md（第7节）

---

## 四、接下来全部该干的事（按优先级）

### P0 — 立即（安全+验证）
1. **用户去飞书开放平台轮换 App Secret**（git历史泄露3次，代码修不了）
2. 启动 Docker Desktop → `make up` → `make test` 验证全栈
3. 为本次4模块补pytest：`test_agent_graph`(tier排序+benchmark)、`test_alpha_social_feishu`(绑定+同步)、`test_diy_cli`(意图解析)、`test_tenant_panel`(面板CRUD+隔离)
4. 基建自替换benchmark接真实调用日志(当前`_success_rate`是占位)

### P1 — DS真功能闭环（9个致命bug）
5. 修DS登录认证绕过(#2) — quick-register不存在→catch直接push /chat
6. 修ProductAiDialog保存旧文案(#3)
7. 修lib/api.ts 15+死方法(#4)
8. 修Layout强制Sidebar(#5)
9. 修brain硬编码Alpha-001→多租户隔离(#6)
10. 修A2A页面假数据+不存在API(#7)
11. 修webhook/shoplazza文件名内容不一致(#8)
12. 修workflow页面API路径(#11)
13. 修settings店铺模式切换(#12)

### P2 — 修正点落地（本次探讨的5个修正）
14. DIY CLI改成adapter层，接Codex/Claude/Aider
15. 基建自替换从每小时改成每天+真实数据打榜
16. benchmark_skill接EventBus真实调用事件
17. AgentGraph加外部skill市场路由源
18. DIY CLI+面板补7个业务场景意图(闲鱼/小红书/抖音/短剧/视频/游戏/文案)

### P3 — 架构盘活
19. OrchestratorEngine注册更多channel/loop(#9) — 接入飞书/Web/NURO渠道
20. mindflow/包接入活跃链路(#10) — 通过EventBus或API路由连通
21. ToolA/ToolB stub→真实接入(PHASE1_PLAN P2-7)
22. verify_shortdrama_e2e.py死代码盘活(引用不存在的tools.shortdrama_tool)

### P4 — 剩余小问题(#13-#25)
23. demo路由错、obsidian URL缺`?`、RevenueChart CSS、StatusBadge不匹配、chat固定话术、AuthGuard过松、catch吞错误、无error boundary、端口三处不一致、内容详情页未实现、feishu-bot Dockerfile COPY未追踪bot.py

### P5 — 打包分发（Untitled.md，完成度不够暂不做）
24. PyInstaller打包Gateway+Orchestrator+Alpha-ID为exe
25. 最简Electron壳嵌入DS前端
26. API Key设置页(用户自填，不硬编码)
27. GitHub Release上传
28. 端口随机化

### P6 — 长期
29. 测试覆盖率10%→60%+
30. wechat.py盘活
31. eventbus-server.ts合并到eventbus-init.ts
32. GitHub Actions多系统自动打包

---

## 五、打包前完成度清单（全部✅才能打包）

- [ ] P0 安全：飞书密钥已轮换+git历史清理
- [ ] P0 Docker全栈healthy
- [ ] P1 DS 25个bug全修
- [ ] P1 测试覆盖率≥40%
- [ ] P1 新增4模块有单测
- [ ] P2 5个修正点落地
- [ ] P2 OrchestratorEngine注册真实channel/loop
- [ ] P2 ToolA/ToolB stub→真实接入
- [ ] P2 mindflow包接入活跃链路
- [ ] P5 用户API Key设置页
- [ ] P5 端口随机化
- [ ] P5 种子数据脚本
- [ ] P5 前置条件检查脚本

---

## 六、项目管理优化建议

### 1. 新模型 onboarding 路径
读本文件 → GHOST.md第1-2节 → PROJECT_STATUS_REPORT第5节 → AGENTS.md → WORK_LOG最后一个Session → DECISIONS最后5条 → 开干

### 2. 探讨→落地追踪
每次会话结束时，把"探讨过但没落地的想法"追加到DECISIONS.md的"待记录决策"部分，下次会话开头检查

### 3. 模块健康度看板

| 模块 | 代码完成度 | 测试覆盖 | 运行时验证 | 健康度 |
|:--|:-:|:-:|:-:|:-:|
| Gateway | 85% | 53 tests | ✅ | A |
| Orchestrator | 40% | 7 tests | ✅ | B |
| Alpha-ID | 45% | 802 tests | ⚠️ | B |
| DS | 60% | 45 tests | ⚠️ | C |
| Nebula | 70% | 153 tests | ⚠️ | B |
| 调度层(新) | 90% | 0 tests | ❌ | D |
| 飞书社交(新) | 90% | 0 tests | ❌ | D |
| DIY CLI(新) | 90% | 0 tests | ❌ | D |
| 多租户面板(新) | 90% | 0 tests | ❌ | D |

---

## 七、关键术语（AGENTS.md TERM规则，不得自创）

OrchestratorEngine | EventBus | AgentGraph | MemoryGraph | TwinBrain | ChannelAdapter | GhostDS | Gateway | DIY CLI | TenantPanel | UserBinding

## 八、铁律（AGENTS.md）

- 死代码是用来盘活的不是删的
- 改代码必须改文档
- 不硬编码端口/密钥
- 不创建第三个 Orchestrator/EventBus
- 不在 `alphaid/projects/src/` 之外创建Python业务逻辑
- 新代码必须用 `OrchestratorEngine` 或 `get_orchestrator()`
- 事件类型必须用 `EventType` 常量，不得硬编码字符串

---

*本文件由 Session 12 创建，用于模型交接。新模型读完此文件后可直接开始工作。*
