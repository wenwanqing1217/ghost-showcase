# Ghost 项目待执行全量工作计划

> 生成日期: 2026-07-26
> 覆盖: 本对话所有审计、设计、方案中已确认但未落地的事项

---

## 一、大扫除（1天）

| # | 任务 | 出自 | 预估 |
|:-:|:-----|:------|:----:|
| 1 | 删除根目录 22 个调试文件 + 2 个 LevelDB 副本 | AUDIT_COMPLETE.md A1/A4 | 10min |
| 2 | git rm 在 alphaid/projects 里已提交的 7 个调试文件 | ALPHAID_AUDIT.md | 10min |
| 3 | 删除根目录 15 个一次性 fix_ 脚本 | AUDIT_COMPLETE.md A3 | 5min |
| 4 | 删除孤立目录 core/ 和 codex-remote/ | AUDIT_COMPLETE.md B5/B6 | 5min |
| 5 | .gitignore 新增 `_doubao*` `fix_*.py` `*final*` 等模式 | 审计发现 | 5min |
| 6 | 清理废弃 .env 文件中的真实密钥 | AUDIT_COMPLETE.md D1 | 5min |

---

## 二、架构修复（3-5天）

| # | 任务 | 出自 | 预估 |
|:-:|:-----|:------|:----:|
| 7 | Registration.py 改用 Container DI（去掉 4 处直连 SQLite） | AUDIT_COMPLETE.md C2 | 1h |
| 8 | 统一两个 alpha_id.db 为单一数据库 | AUDIT_COMPLETE.md C1 | 1h |
| 9 | Gateway 生产环境 CORS 白名单 | AUDIT_COMPLETE.md D3 | 30min |
| 10 | 修复 mindflow/agents/travel.py 硬编码的百度地图密钥 | ALPHAID_AUDIT.md | 5min |
| 11 | 删除 git 子模块残留配置 (.git/config) | 审计发现 | 5min |
| 12 | 可观测性接入 FastAPI 中间件 | STRATEGY.md §8-10 | 1天 |
| 13 | 故障恢复接入 Gateway | STRATEGY.md §8-11 | 1天 |
| 14 | 补充全局请求限流 | AUDIT_COMPLETE.md D4 | 1天 |

---

## 三、Alpha-ID 接通（1周）

| # | 任务 | 出自 | 预估 |
|:-:|:-----|:------|:----:|
| 15 | AgentLoop + TwinBrain 接入 API 路由 | STRATEGY.md §8-1/2 | 2天 |
| 16 | A2A 协议接入 Gateway | STRATEGY.md §8-3 | 2天 |
| 17 | 采集器（chatgpt/claude/trae 等）接入注册后流程 | ALPHAID_AUDIT.md | 2天 |
| 18 | 测试修复：37 个测试文件在不用 --noconftest 时能正常收集 | AUDIT_COMPLETE.md E1 | 1天 |
| 19 | 跑通一次 GitHub Actions CI | AUDIT_COMPLETE.md E2 | 1天 |

---

## 四、Ghost.html 重构（1周）

| # | 任务 | 出自 | 预估 |
|:-:|:-----|:------|:----:|
| 20 | 拆 ghost.html 为 3 文件（.html / .css / .js） | ARCHITECTURE_REDESIGN.md §5 | 1天 |
| 21 | 重构侧边栏为 A2A 生态区模式（四层 Agent） | ARCHITECTURE_REDESIGN.md §3 | 2天 |
| 22 | 控制台首页：展示四层 Agent 状态 | ARCHITECTURE_REDESIGN.md §3.1 | 2天 |
| 23 | Mindflow 作为"人机协作模式"接入 | ARCHITECTURE_REDESIGN.md §4 | 2天 |
| 24 | 删除旧的"Web4.0"和"生态圈"字眼 | 已部分完成，确认全部清除 | 30min |

---

## 五、品牌统一（1天）

| # | 任务 | 出自 |
|:-:|:-----|:------|
| 25 | 确认对外统一品牌名 = Ghost | 战略建议 |
| 26 | Alpha-ID、Mindflow、Nebula 降为内部名称，不对外暴露 | 战略建议 |
| 27 | 更新 README.md 和 GHOST.md 的品牌表述 | 战略建议 |

---

## 六、冷启动设计（2-3天）

| # | 任务 | 出自 | 预估 |
|:-:|:-----|:------|:----:|
| 28 | 设计注册后"啊哈时刻"体验 | 战略建议 | 1天 |
| 29 | 例如：注册后自动采集 ChatGPT 数据 → 生成记忆图谱 | 战略建议 | 2天 |
| 30 | 确保新用户在 30 秒内体验到"这是你的数字痕迹" | 战略建议 | — |

---

## 七、运维准备（可并行）

| # | 任务 | 出自 |
|:-:|:-----|:------|
| 31 | 选定 Python 后端部署方案（Railway/Fly.io/服务器） | STRATEGY.md Phase 2 |
| 32 | SQLite → PostgreSQL 迁移方案 | STRATEGY.md Phase 2 |
| 33 | 接入 Sentry 错误监控 | 战略建议 |
| 34 | 编写隐私政策 + 用户协议 | AUDIT_COMPLETE.md G3 |
| 35 | 制定 775 个测试用户的迁移/清理策略 | 新增 |
| 36 | 接入开源 LLM 备选（规避闭源风险） | Web4.0文档 |

## 八、遗漏补录

| # | 任务 | 出自 | 预估 |
|:-:|:-----|:------|:----:|
| 37 | ghost-capture/ 豆包浏览器扩展重建 | GHOST_DOUBAO_DESIGN.md | 2天 |
| 38 | mindflow/voice_control.py 语音控制接入 | 代码审计发现 | 2天 |
| 39 | .github/ISSUE_TEMPLATE/ + dependabot.yml 配通 | 审计发现 | 1h |
| 40 | 端到端测试：注册 → 登录 → 存入记忆 → 查询返回 | STRATEGY.md | 1天 |
| 41 | 更新 GHOST.md + STRATEGY.md + STARTUP.md 架构文档 | 每次重构后更新 | 持续 |
| 42 | 为新功能（A2A、Mindflow、采集器）补充测试 | 新增 | 持续 |

## 十、数据主权与合规

| # | 任务 | 出自 | 预估 |
|:-:|:-----|:------|:----:|
| 43 | 用户数据删除/导出功能（《个保法》要求） | 战略合规 | 2天 |
| 44 | 双链私链加密存储容灾恢复 | 战略合规 | 2天 |
| 45 | API 密钥轮换流程文档（阿里云/支付宝/DeepSeek） | 战略合规 | 1天 |
| 46 | 隐私政策 + 用户协议撰写 | AUDIT_COMPLETE.md G3 | 2天 |

## 十一、工程质量

| # | 任务 | 出自 | 预估 |
|:-:|:-----|:------|:----:|
| 47 | Ghost.html 按需加载（当前 4300 行首屏全量加载） | 工程质量 | 1天 |
| 48 | 统一日志收集（3 个服务各自写文件，无中心） | 工程质量 | 1天 |
| 49 | API 版本号策略（当前无版本前缀控制） | 工程质量 | 1天 |
| 50 | 依赖安全漏洞扫描（npm audit + pip audit） | 工程质量 | 1天 |
| 51 | 前端移动端适配验证 | 工程质量 | 1天 |
| 52 | 键盘导航 + 屏幕阅读器支持 | 合规 | 2天 |
| 53 | 国际化准备（当前全中文硬编码） | 工程质量 | 2天 |

## 十二、功能缺失

| # | 任务 | 出自 | 预估 |
|:-:|:-----|:------|:----:|
| 54 | 邮箱注册 + 密码重置 | 功能缺失 | 1天 |
| 55 | CLI 命令与 Web 注册用户状态统一 | 功能缺失 | 2天 |
| 56 | 恢复 CONTRIBUTING.md 社区贡献指南 | 功能缺失 | 1天 |

## 十三、用户体验问题

| # | 任务 | 出自 | 预估 |
|:-:|:-----|:------|:----:|
| 57 | 飞书机器人 WebSocket 心跳保活修复 | 用户反馈 | 1天 |
| 58 | 飞书对话上下文管理（session_id + 历史加载） | 用户反馈 | 2天 |
| 59 | 总助模式切换：`/agent/switch` 或独立 endpoint | 用户反馈 | 2天 |

## 十三、总计

| 阶段 | 任务数 | 预估总工期 |
|:-----|:------:|:----------:|
| 大扫除 | 6 | 1天 |
| 架构修复 | 8 | 3-5天 |
| Alpha-ID 接通 | 5 | 1周 |
| Ghost.html 重构 | 5 | 1周 |
| 品牌统一 | 3 | 1天 |
| 冷启动 | 3 | 2-3天 |
| 运维准备 | 6 | 可并行 |
| 遗漏补录 | 6 | 可并行 |
| 数据主权与合规 | 4 | 可并行 |
| 工程质量 | 7 | 可并行 |
| 功能缺失 | 3 | 可并行 |
| **合计** | **56** | **约 4-6 周** |
