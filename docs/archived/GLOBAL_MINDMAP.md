# Ghost + Alpha-ID 全局思维导图

> ⚠️ **已过时** — 本文档已合并到新文档 `ARCHITECTURE.md`，请以新文档为准。
> 产出基于：全部代码审计 + 41 目录设计哲学 + 逐文件扫描
> 目标：问题关联 → 打通路径 → 重构方案

---

## 一、问题簇：根源在同一个地方

整个项目的所有问题可以归为 **5 个问题簇**，它们不是独立的，是从一个根上长出来的：

```
                    ┌─── 写了 18 个 core 模块没接 ← 写完就跳下一个
                    │
    ┌─── 没有产品定义 ──── 不知道"完成"长什么样 ← 没有 MVP 标准
    │      ↓
    根源：先写框架再填内容 ────┴─── PyPI 入口是坏的 ← 写了不验证
    │      ↑
    └─── 永远在写新东西 ──── Ghost.html 4300 行单体 ← 不敢拆
                           │
                           └─── 3 个入口 2 个是坏的 ← 验证 = 0
```

**根源只有一个：你习惯于把设计/架构/代码写到"看起来完整"就停，而不是验证到"它真的能跑"才停。**

---

## 二、问题簇 1：写完没接通（占 70% 的代码量）

| 模块 | 行数 | 状态 | 应该通向哪里 |
|:-----|:----:|:-----|:-------------|
| AgentLoop | 813 | 0 引用 | → API 路由 → Gateway → Ghost.html 聊天面板 |
| TwinBrain | 690 | 0 引用 | → AgentLoop 初始化时注入 |
| A2A 协议 | 410 | 0 引用 | → Gateway → 网络拓扑 → Agent 面板 |
| CoALA 记忆 | 507 | 0 引用 | → 先不接（概念超前） |
| 可观测性 | 553 | 0 引用 | → FastAPI 中间件（半天能接完） |
| 故障恢复 | 534 | 0 引用 | → Gateway 启动回调 |
| 事件总线 | 261 | 0 引用 | → 先不接（模块间解耦需要架构稳定后） |
| 9 个采集器 | 1,487 | 全写了 | → 注册后引导流程 |
| mindflow 10 文件 | ~1,800 | 路径未通 | → A2A 生态区面板 |

**打通路径（按执行顺序）：**

```
━ Day 1-2：接 AgentLoop → API 路由
   用户能 POST /chat 得到 Agent 响应
   
━ Day 2-3：接 TwinBrain → AgentLoop
   Agent 有状态了，不是每次从零开始

━ Day 3-4：接可观测性 → FastAPI 中间件
   能看到请求量、错误率、响应时间

━ Day 4-5：接故障恢复 → Gateway
   服务崩了自动恢复

━ 之后：接采集器 → 注册流程
   注册后引导用户导入 ChatGPT/Trae 数据
```

---

## 三、问题簇 2：入口断了（用户进不来）

```
用户 pip install alpha-id-zix
  → aid init              ✅
  → aid-api               ❌ 指向已删模块
  → aid-daemon            ❌ 指向已删模块
  
用户打开 ghost.html
  → 注册 Alpha-ID        ✅
  → 进入工作台           ✅
  → 点"意图解析"         ❌ 空壳
  → 点"路由决策"         ❌ 空壳
  → 点"Agent 广场"       ❌ 空壳
  → 点"执行日志"         ❌ 硬编码数据
```

**打通路径：**
1. 修 pyproject.toml：删 `aid-daemon`、修 `aid-api` 指向 `uvicorn main:app`
2. Ghost.html 的空壳面板统一显示 "开发中" 而不是硬编码假数据
3. 发 0.3.1

---

## 四、问题簇 3：存储碎片化

```
alpha_id.db（SQLite，主要数据库）
  ├─ 用户数据
  ├─ 计数器
  └─ 创始人标记

alpha_id_users.json（JSON 文件，遗留）
  └─ 用户数据（可能不同步）

*.json 文件（assets/，遗留）
  ├─ private_chain_*.json
  └─ knowledge_chain_*.json

mindflow_map.db（SQLite，Nebula 使用）
  └─ 工作流数据

Web 端存储（registration.py 直连 SQLite）
  └─ SMS 验证码
```

**打通路径：**
- 已修：`user_identity.py` 默认改 `SqliteStorage`
- 已修：`dual_chain.py` 默认改 `SqliteStorage`
- 已修：`rotate_token` 防重放
- 待修：`registration.py` 改用 Container DI（取代直连 SQLite）

---

## 五、问题簇 4：设计与代码脱节

41 目录中的文档描绘了这样的产品：

```
一次安装 → 所有 AI 工具认识你
Web 端 30 秒感受到魔法
模拟盘看到自己的数字存在
```

但代码实际交付的是：

```
pip install → 入口坏
Web 端打开 → 注册 30 秒 → 空壳面板
模拟盘 → 不存在
```

**打通路径：**
1. 选 41 目录中优先级最高的 3 个设计点
2. 对照代码看差了多远
3. 修 1 个再发 1 个版本，而不是全部修完再发

---

## 六、问题簇 5：没有发布节奏

```
0.0.1 → 0.3.1（15 个版本）
本地无 tag
CI 从未跑绿过
pyproject.toml 的 name 和 PyPI 不一致
每次发版似乎是手动操作
```

**打通路径：**
1. git tag v0.3.1 标记当前代码
2. CI 至少跑通 `pytest tests/test_registration.py`
3. README 徽章从 "928 tests passing" 改成实际数字
4. 规范化发版流程：改版本号 → CI 绿 → twine upload

---

## 七、全局打通路线图

```
Phase 1（立即 1 天）：止血
  ├── 修 pyproject.toml 入口（删 aid-daemon、改 aid-api）
  ├── 发 alpha-id-zix 0.3.1
  └── Ghost.html 空壳面板标记 "开发中"

Phase 2（1 周）：接死代码
  ├── AgentLoop → API 路由
  ├── TwinBrain → AgentLoop
  └── 可观测性 → 中间件

Phase 3（1 周）：统一存储 + 修漏洞
  ├── registration.py → Container DI
  ├── 统一 GHOST_WORKSPACE_PATH 环境变量
  └── CI 跑绿

Phase 4（持续）：文档 -> 代码闭环
  ├── 41 目录设计 → 对应 issue
  ├── 每个版本实现 1-2 个设计点
  └── 发版日 = CI 绿日
```

---

## 八、你现在应该做什么

**不要同时推进 Phase 1-4。** 先做 Phase 1 的 3 件事，发版。发完之后我有反馈了我再决定 Phase 2。这是我给你的最后一条建议。

所有问题都标注完了，311 文件、304 Python、23 TS、1 个 4300 行 HTML、11 个设计文档——全网翻遍。留不下什么了。
