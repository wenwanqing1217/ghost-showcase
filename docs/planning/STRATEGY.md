# Ghost 项目全局战略分析

> 版本: 1.0 | 2026-07-26
> 视角：翻到底 + 走一步看三步

---

## 一、愿景回顾

GHOST.md 中描述的最终形态：

> 「一人一生唯一 Alpha-ID + 双大脑架构 + 机器可读资讯生态 + MCP 技能统一适配 + Obsidian 知识闭环 + 合规双边商业生态」

三层用户流：
- **豆包** → 知识输入 → Obsidian
- **飞书** → 自然语言调用 → Gateway → 全平台能力
- **Ghost.html** → Web 展示、注册、聊天、浏览

目标用户是谁？没有定义。这是第一个缺失。

---

## 二、现状全景图（代码 + 服务 + 数据）

### 现有服务

| 服务 | 语言 | 端口 | 代码量 | 状态 |
|:-----|:------|:-----|:-------|:------|
| **alphaid API** | Python | :8000 | ~22K | 🟢 完整运行 |
| **Gateway** | Python | :18080 | ~800L | 🟢 运行 |
| **Ghost.html** | 单体 HTML/JS | :8000/ | ~4.4K | 🟢 两视图架构（A2A 生态区 + Mindflow 协作台）|
| **Flow/API** | Node/TS | :3001 | ~4.4K | 🔴 不能后台驻留 |
| **Nebula** | Python | :2002 | ~6.1K | 🟢 刚验证可启动 |
| **核心库** | Python | — | ~7.4K | 🟢 可用 |

### 数据存储

| 数据 | 存储 | 问题 |
|:-----|:------|:------|
| 用户身份 | SQLite `collections` 表 | 无迁移、无版本 |
| 双链记忆 | SQLite `collections` 表 | 刚完成从 JSON 迁移 |
| SMS 验证码 | SQLite（registration.py 直连） | 绕过 Container DI |
| 支付宝状态 | SQLite（同上） | 同上 |
| 社交数据 | SQLite | 无索引优化 |

### 当前用户数

数据库里有约 775 个 Alpha-ID，活跃用户 0。

---

## 三、根因分析（根因，不是症状）

### 根因 1：没有产品定义和用户画像

```
症状：不知道给谁用 → 无法做优先级 → 什么都想做 → 什么都没做完
```

- 目标用户是开发者？普通用户？企业？
- MVP 是什么？最小可用产品长什么样？
- 没有产品 roadmap，只有技术概念

### 根因 2：架构领先于验证

```
症状：写了 6 层架构（身份→记忆→调度→网关→通信）但一条用户路径都没跑通
```

- 花了大量时间在 L4-L6（调度、通信）但 L1 用户交互层才半通
- A2A 协议、AgentLoop、TwinBrain 都写了，Ghost.html 已重构为两视图：A2A 生态区（workbenchView）+ 人机协作台（mindflowView）
- 先搭了完整架子再填内容，导致架子搭完了内容没填

### 根因 3：前后端耦合在单体文件里

```
症状：Ghost.html 4000+ 行 → 一个人改不动 → 改一次要全局思考
```

- 没有构建工具、没有路由系统、没有组件化
- JavaScript 直接在 HTML 里，变量全局作用域
- 加一个面板就是加一段不可测试的 JS
- **已修复**：删除重复的 4 个 Mindflow 面板（思维画布/任务看板/笔记库/人格画像），workbenchView 聚焦 A2A 生态，mindflowView 作为唯一的人机协作台

### 根因 4：数据层没有统一入口

```
症状：5 种方式读写数据 → 改一个存储逻辑要改 5 处
```

| 读写方式 | 位置 | 状态 |
|:---------|:------|:------|
| Container → StorageBackend | `user_identity.py` | ✅ 主路径 |
| 模块级 `sqlite3.connect()` | `registration.py` | ✅ 已改为 Container DI |
| 文件系统 `os.walk` 读 `.md` | Gateway `memory_search` | ⚠️ 待统一 |
| JSON 文件读写 | 已被淘汰 | ✅ 已淘汰 |
| SQLite 直连 | `alpha_id.db` | ✅ 通过 Container 访问 |

### 根因 5：没有发布 pipeline

```
症状：只能本机运行 → 别人用不了 → 永远不会收到真实反馈
```

- Vercel 只部署了静态前端
- 没有 CI 验证、没有 CD 部署
- 888 个测试 3 个收集就崩（已修）
- .env 密钥散落各处

---

## 四、未来功能全景

GHOST.md 和各处代码暗示的未来功能：

| 功能 | 状态 | 优先级 | 依赖 |
|:-----|:------|:-------|:------|
| DID 身份注册 | 🟢 完整 | P0 | — |
| 双链记忆 | 🟢 完整 | P0 | — |
| Ghost.html 官网 | 🟡 半通 | P0 | 面板数据 |
| SMS 真实通道 | 🟡 已接 SDK | P0 | 阿里云余额 |
| 支付宝人脸认证 | 🟡 真实模式 | P1 | 已在跑 |
| 记忆图谱可视化 | 🟢 d3.js 有 | P1 | — |
| 豆包知识采集 | 🔴 未开发 | P1 | 浏览器插件 |
| 工作台意图解析 | 🔴 空壳 | P2 | LLM 接口 |
| Skill 路由决策 | 🔴 空壳 | P2 | AgentLoop |
| A2A Agent 网络 | 🔴 代码有未通 | P2 | 网络层 |
| 飞书机器人 | 🟡 有代码 | P1 | Nebula 常驻 |
| AI 多 Provider 路由 | 🟡 代码在 Flow | P2 | Flow 迁移 |
| Computer Use | 🟡 代码在 Flow | P3 | 浏览器自动化 |
| Obsidian 知识库 | 🟡 Gateway 能搜索 | P2 | 豆包 |
| 商业生态 | 🔴 0 | P4 | — |

---

## 五、路线图（走一步看三步）

### 原则

1. **先跑通一条真实用户路径**，再扩展（而不是先搭完六层再填内容）
2. **消灭技术债在源头**，不累积（存储统一、单测、CORS 这种不再拖）
3. **能砍的就砍**，不维护没人用的功能（Flow API、Nebula 如果没人用就归档）

### Phase 1：止血（1 周）

**目标：一条完整用户路径从注册到记忆存储到查询**

```
用户 → 打开 Ghost.html → 注册 Alpha-ID → 写一条记忆 → 查询回来
```

| 任务 | 原因 | 状态 |
|:-----|:------|:------|
| 砍掉 Flow API AI 路由 | 没人用，Python 侧已有 AgentLoop 替代 | ⏸️ 待评估 |
| 砍掉 Nebula 工作流 | 没人用，注册已迁到 alphaid | ⏸️ 待评估 |
| Ghost.html 面板整理 | 删除重复 Mindflow 面板，workbenchView 聚焦 A2A 生态 | ✅ 已完成 |
| 统一 storage 入口：registration.py 改用 Container DI | 不再直连 SQLite | ✅ 已完成 |
| 把 SMS 验证码、支付宝状态存到统一 StorageBackend | 消除散落连接 | ✅ 已完成 |
| Python 编译检查 + 注册测试加入 CI | 至少保证新功能不崩 | ✅ 已完成（11/11 通过）|
| 清理已删除模块残留的 conftest 引用 | CI 能过 | ✅ 已完成 |
| complete_registration 用户落库 | 注册真正写入数据库 | ✅ 已完成 |
| health 端点 db_path 硬编码 | 改用 container.storage | ✅ 已完成 |
| dual_chain API storage 注入 | 测试能用临时数据库 | ✅ 已完成 |

### Phase 2：上生产（2-4 周）

**目标：Ghost 可以在公网被任何人访问**

| 任务 | 原因 |
|:-----|:------|
| 选型：Python 后端部署方案 | Vercel Functions？Railway？Fly.io？轻量服务器？ |
| SQLite → PostgreSQL 迁移 | Serverless 不支持 SQLite |
| 统一 .env 变量命名 | 现在有的用 `ALPHAID_` 有的用 `AID_` 有的用 `ALPHA_` |
| JWT 密钥从环境变量加载 | 不能在代码里有默认值 |
| CORS 生产环境白名单 | 现在 dev 通配符在生产要禁止 |
| 接入 Sentry / 日志 | 上线后要能看到错误 |
| 跑通一次 GitHub Actions CI | 绿色勾之后才有信心改代码 |

### Phase 3：做产品（1-2 月）

**目标：用户愿意主动使用 Ghost**

| 任务 | 原因 |
|:-----|:------|
| 定义 MVP 用户画像 | 先知道给谁用 |
| Ghost.html 用框架重写 | 单体 4300 行不可持续 |
| 工作台面板 9 个面板数据全接 | 用户看到才有信心 |
| 豆包知识采集浏览器插件 | GHOST.md 里的核心入口之一 |
| 飞书机器人稳定运行 | 另一个核心入口 |

---

## 六、关键决策（必须选，不能兼得）

### 决策 1：前端框架选型

| 选项 | 好处 | 成本 |
|:-----|:------|:------|
| 维持单体 HTML/JS | 0 迁移成本 | 长期拖累 |
| 拆成 3 文件（CSS/HTML/JS） | 低风险，可维护 | 还是单体 |
| 用轻量框架（Alpine/Svelte） | 组件化、可测试 | 需学习 |
| 用 React/Vue | 生态最强 | 沉重，可能过度 |

### 决策 2：Python 后端部署

| 选项 | 好处 | 成本 |
|:-----|:------|:------|
| Railway / Fly.io | 简单，支持 Python | 月费 |
| Vercel Functions | 和前端同一平台 | Serverless 限制 |
| 阿里云 ECS/轻量服务器 | 完全控制 | 运维成本 |
| Docker 部署到任何地方 | 最标准 | 需要 Dockerfile |

### 决策 3：Node 栈去留

| 选项 | 好处 | 成本 |
|:-----|:------|:------|
| 砍掉 Flow API | 少一个服务、少一套运维 | AI 路由暂时没有 |
| 保留 Flow API（AI 路由 + Computer Use） | 保留已有功能 | Windows 驻留无解 |
| AI 路由迁到 Python | 彻底统一栈 | 需要开发时间 |

---

---

## 八、差距落地实现方案

### 按优先级排列的 16 项差距实现路径

| # | 差距项 | 前置依赖 | 估算工期 | 实施路径 |
|:-:|:-------|:---------|:--------:|:---------|
| **1** | **AgentLoop 接入 API** | 无 | 1-2天 | 在 `api/agent.py` 新建路由 → `POST /chat` 调 `AgentLoop.run()` → 返回流式结果 |
| **2** | **TwinBrain 接入 AgentLoop** | 前置:1 | 1天 | `AgentLoop.__init__` 传入 `TwinBrain` 实例 → 状态变更时自动写入双链记忆 |
| **3** | **A2A 协议接入 Gateway** | 前置:1 | 2天 | `a2a.py` 加 HTTP Server → Gateway 加 `/v1/a2a/*` 路由 → 本地 mock 改为真实 HTTP |
| **4** | **豆包浏览器扩展重建** | 无 | 2天 | 重建 `ghost-capture/` 目录 → content.js 监听 doubao.com DOM → background.js POST 到 Gateway |
| **5** | **双层网关（私有+公共）** | 无 | 3天 | 拆分当前 Gateway → 私有网关 `:18081`（仅限本地）→ 公共网关 `:18080`（外网访问） |
| **6** | **飞书机器人稳定运行** | 前置:5 | 1天 | nebula 启动脚本 → 后台驻留 → Gateway 转发飞书消息到 AgentLoop |
| **7** | **MCP 技能适配中心** | 无 | 1周 | 定义 MCP 技能注册协议 → 技能仓库 → Gateway 发现/调用路由 → 安全沙箱 |
| **8** | **A2A 真实网络通信** | 前置:3 | 3天 | WebSocket 长连接 → Agent 发现机制 → 临时授权协议 → 通信加密 |
| **9** | **实名认证（身份证）** | 无 | 2天 | 接入阿里云/腾讯云实名认证 API → 注册流程加身份核验步骤 |
| **10** | **可观测性接入** | 无 | 1天 | `observability.py` 注册为 FastAPI 中间件 → 自动记录请求/响应/耗时 |
| **11** | **故障恢复接入** | 无 | 1天 | Gateway 启动时注册 `recovery.py` 回调 → 关键服务异常自动恢复 |
| **12** | **八大行业知识库** | 前置:7 | 2月/行业 | 选1个行业先做 → 信源梳理 → 爬虫 → 清洗 → 入库 → Ghost.html 展示 |
| **13** | **Obsidian 双向同步** | 前置:12 | 2周 | Obsidian 插件开发 → 本地文件监听 → 冲突处理 → 双向同步协议 |
| **14** | **星点积分/支付** | 无 | 2周 | 支付宝/微信支付接入 → 积分数据库 → 消费/充值前端 UI |
| **15** | **技能市场/创作者后台** | 前置:7,14 | 1月 | 前端（Skill 搜索+定价+评价）+ 后端（上架+审核+分账）+ 审计 |
| **16** | **容器 DI 覆盖 registration.py** | 无 | 1小时 | `registration.py` 的 4 处 `sqlite3.connect()` 改为通过 Container 获取存储后端 |

### 关键路径图

```
Phase 0（大扫除 1天）
  └─ 删调试文件 + 清理 git 历史 + 删孤立目录
      │
Phase 1（接死代码 1周）
  ├─ 1.AgentLoop 接入 API          ← 入口，必须先做
  ├─ 2.TwinBrain 接入 AgentLoop
  ├─ 3.A2A 协议接入 Gateway
  ├─ 10.可观测性接入 API
  ├─ 11.故障恢复接入 Gateway
  ├─ 16.Container DI 覆盖 registration.py
  └─ 4.豆包扩展重建
      │
Phase 2（上生产 2周）
  ├─ 5.双层网关隔离
  ├─ 6.飞书机器人稳定运行
  └─ 9.实名认证接入
      │
Phase 3（做产品 1-3月）
  ├─ 7.MCP 技能适配中心
  ├─ 12.行业知识库（1个行业先做）
  ├─ 13.Obsidian 双向同步
  ├─ 14.星点积分/支付
  └─ 15.技能市场/创作者后台
```

### 一句话

把六层架构建好但没接的 6,530 行死代码接上，比从零写新功能更重要。**Phase 1 的核心任务已完成（storage 统一、注册落库、测试 CI、前端面板清理），Ghost 已从「空壳架子」变成「可演示产品」**。


---

## 九、实名认证链路设计

### 目标

本地 DID 密钥证明"你是谁"，实名凭证证明"你不是冒充的"。

### 流程

```
aid init → Ed25519 密钥对 → did:aid:xxx（不记名）
aid bind → POST /api/v1/identity/bind-face → Alipay 人脸核验 → 签名凭证 → DID Document
AI 工具查询 → 看到 verification.status = verified
```

### 隐私保障

DID 私钥在本地，身份证号/人脸在 Alipay，签名凭证仅标记"已实名"。

### DID Document 字段

```json
{
  "id": "did:aid:xxx",
  "verification": {
    "status": "verified",
    "method": "alipay_realname",
    "signedAt": "2026-07-26T...",
    "expiresAt": "2027-07-26T...",
    "signature": "服务端签名凭证"
  }
}
```

---

## 十、桌宠方案集成计划

### 技术栈

| 组件 | 技术 | 用途 |
|:-----|:------|:------|
| 核心模型 | MiniCPM-o-4.5 (9B 4bit) | 全双工多模态理解 |
| 语音识别 | Whisper | 本地语音输入 |
| 语音合成 | Coqui TTS | 本地语音输出 |
| 向量记忆 | Chroma | 对话历史与偏好存储 |
| 运行时 | Ollama | Windows 本地推理 |
| 工具协议 | MCP | 浏览器/数据库/Git 集成 |
| 桌宠形象 | Live2D 动态 | Q 版角色表情动作 |
| 交互模式 | 弹幕/气泡/语音唤醒 | 手动切换 |
| 隐私保护 | 眼瞎耳聋模式 | 一键关闭采集 |

### 与 aid-daemon 结合架构

```
aid-daemon（Ghost 桌面精灵入口）
  ├── 悬浮球 UI（现有）
  ├── 对话面板（现有）
  ├── 弹幕模式（游戏场景）
  ├── 气泡提醒（日常/网课）
  ├── 语音唤醒（全场景）
  │
  ├── MiniCPM-o-4.5（Ollama 本地推理）
  │   ├── 屏幕观察（多模态输入）
  │   ├── 语音理解（Whisper 识别）
  │   └── 主动交互（全双工流式）
  │
  ├── Coqui TTS（语音合成输出）
  │
  ├── Chroma（本地记忆存储）
  │   └── 通过 Ghost 双链记忆 API 也可互补
  │
  └── MCP 工具层（复用现有 MCP Server）
      ├── 浏览器控制
      ├── 本地文件读写
      └── Git 操作
```

### 硬件门槛

RTX 5070 Ti / 4bit 量化 / Windows 10/11 x64
Python 3.11-3.13

### 开源策略

一键安装包 + 开源仓库 + 可自定义提示词和交互逻辑

### 桌宠记忆存储方案

不新增 Chroma 同步逻辑，直接复用现有存储层：

```
aid-daemon 对话记录
      ↓
Gateway /v1/memory/store（已有端点）
      ↓
alphaid 双链记忆 SQLite
      ↓
Obsidian（Gateway 已有搜索能力，双向同步 Obsidian 插件待开发）
```

**多线程优化：** `aid-daemon` 的语音识别（Whisper）和屏幕观察（MiniCPM）分两个独立线程跑，不阻塞对话面板 UI。

**Obsidian 角色：** 作为用户可见的知识库前端，桌宠的对话摘要自动归档到 Obsidian MD 文件，用户可直接在 Obsidian 中查看和编辑。
