<!-- STATUS: ACTIVE -->

# Content Generation Pipeline — 设计文档

> **日期**: 2026-08-05  
> **状态**: Proposed  
> **关联**: GHOST.md（愿景）, DECISIONS.md（决策记录）, PROJECT_STATUS_REPORT.md（状态）

---

## 0. 背景

电商业务（OneBound/Shoplazza/商品/订单）对用户没有实际价值——没有店铺、没有货源、没有环境。但平台上已跑通的链路（Gateway → Alpha-ID → TwinBrain → LLM + Feishu Bot + EventBus）是真实在用的 AI 基础设施。

**结论：Ghost Platform 的实际定位不是电商平台，是"一句话生成内容并发布"的创意平台。** 电商数据模型保留在数据库，但前端展示和用户交互的核心要转向内容生成。

---

## 1. 总体架构

```
用户（飞书 / Web / 语音）
  │
  ▼
┌─ 输入层 ─────────────────────────────────────────────┐
│  飞书 Bot (bot.py)  │  Ghost DS (Next.js)  │  其他   │
└──────────────────────┼──────────────────────┼────────┘
                       │                      │
                       ▼                      ▼
                ┌─ 内容生成层 ──────────────────────┐
                │                                   │
                │  视频生成                          │
                │  MoneyPrinterTurbo (:8080)        │
                │  DeepSeek 写脚本 → 素材 → 合成    │
                │                                   │
                │  游戏生成                          │
                │  GameEngine (LLM Pipeline)        │
                │  DeepSeek 设计规格 → 代码 → 审查  │
                │                                   │
                └───────────────┬───────────────────┘
                                │
                                ▼
                ┌─ 内容存储层 ──────────────────────┐
                │                                   │
                │  /ghost-content/                   │
                │    videos/  ← 视频文件 + 封面      │
                │    games/   ← HTML5 游戏 + 封面    │
                │                                   │
                │  PostgreSQL ds schema              │
                │    Product.contentType             │
                │    Product.videoUrl / gameUrl       │
                │                                   │
                └───────────────┬───────────────────┘
                                │
                                ▼
                ┌─ 展示层 ──────────────────────────┐
                │                                   │
                │  飞书卡片                           │
                │    Card Video（内嵌播放器）          │
                │    Card Iframe（游戏直接跑）         │
                │                                   │
                │  Ghost DS                          │
                │    内容浏览页（卡片网格）             │
                │    视频卡片 / 游戏卡片               │
                │                                   │
                └───────────────────────────────────┘
                                │
                                ▼
                ┌─ 通知层 ──────────────────────────┐
                │                                   │
                │  EventBus (Redis Streams)          │
                │    video:generated → 飞书通知       │
                │    game:generated  → 飞书通知       │
                │                                   │
                └───────────────────────────────────┘
```

---

## 2. 视频生成方案

### 2.1 工具选型

| 工具 | 类型 | CLI/API | 费用 | 质量 | 选择 |
|:-----|:-----|:--------|:-----|:-----|:-----|
| **MoneyPrinterTurbo** | 完整视频生成工具 | REST API + CLI | 免费（自部署） | ⭐⭐⭐⭐ | ✅ **选这个** |
| Runway Gen-4 | API 服务 | REST API | $12/月 | ⭐⭐⭐⭐⭐ | 备选 |
| Wan2.1 1.3B | 开源模型 | CLI | 免费（需 GPU） | ⭐⭐⭐ | 备选 |

**选择 MoneyPrinterTurbo 的理由：**
- 完整管道（LLM 写脚本 → 素材匹配 → 字幕 → BGM → 合成），不需要自己搭
- 支持 DeepSeek（用户已有）
- 免费自部署
- 四种接口：WebUI / REST API / CLI / AI Agent
- 输出 9:16 竖屏和 16:9 横屏

### 2.2 MoneyPrinterTurbo 部署

```bash
# 部署到 Ghost Platform 基础设施
git clone https://github.com/harry0703/MoneyPrinterTurbo.git
cd MoneyPrinterTurbo

# 配置（config.toml）
#   LLM provider = deepseek
#   DeepSeek API key = 用户已有
#   TTS = edge（免费，无需 key）

# Docker 启动（推荐）
docker compose up -d

# 或本地 Python 3.11+
pip install -r requirements.txt
python main.py
```

**服务地址**: `http://localhost:8080`  
**API 端点**: `POST /api/v1/video/generate`

### 2.3 视频生成 API

```json
// 请求
POST /api/v1/video/generate
{
  "prompt": "日本赛博朋克风格的城市雨夜，霓虹灯倒映在积水的地面上",
  "video_aspect": "16:9",
  "video_concat_mode": "random",
  "language": "zh"
}

// 响应
{
  "task_id": "abc123",
  "status": "completed",
  "video_url": "/ghost-content/videos/abc123.mp4",
  "cover_url": "/ghost-content/videos/cover_abc123.jpg",
  "duration": 45,
  "script": "生成的完整脚本..."
}
```

### 2.4 Gateway 代理路由

新增 `POST /v1/content/video/generate`，代理到 MoneyPrinterTurbo API：

```python
# ghost-main/gateway/routes/content.py（新建）
@router.post("/v1/content/video/generate")
async def generate_video(request: VideoGenerateRequest):
    # 1. 验证用户身份（X-Tenant-ID + JWT）
    # 2. 转发到 MoneyPrinterTurbo API
    # 3. 返回视频 URL
    pass
```

---

## 3. 游戏生成方案

### 3.1 工具选型

| 方案 | 说明 | 可行性 |
|:-----|:-----|:-------|
| Unity CLI | 编译器，不是生成器。需要已有 Unity 项目 | ❌ 不适用 |
| Godot CLI | 同 Unity 的问题 | ❌ 不适用 |
| **LLM Pipeline（DeepSeek V4 Flash）** | 纯 LLM 生成 HTML5 游戏代码，五步管道 | ✅ **选这个** |
| 专用游戏生成 CLI | 市场不存在成熟工具 | ❌ |

**选择 LLM Pipeline 的理由：**
- 游戏代码本质是文本，是 LLM 的天生领域
- DeepSeek V4 Flash 编码能力强（Terminal Bench 82.7）
- HTML5 输出 → 飞书 iframe 直接玩，零摩擦
- ZIP 打包 → 用户下载带走
- 五步质量管道保障"精品"输出

### 3.2 GameEngine 服务设计

新建 `ghost-main/game-engine/` 服务（不是 CLI wrapper，是 LLM Pipeline）：

```
ghost-main/game-engine/
  ├── service.py          # GameEngine 主类
  ├── prompts/            # 5 套 prompt 模板
  │   ├── design_spec.md
  │   ├── code_generate.md
  │   ├── code_review.md
  │   ├── code_optimize.md
  │   └── video_script.md
  ├── models.py           # GameResult, DesignSpec, ReviewReport
  ├── validator.py        # Playwright 自动化验证
  └── main.py             # FastAPI 服务入口
```

### 3.3 五步质量管道

```
Step 1: 设计规格生成（LLM）
  Input:  "做一个太空射击游戏，精品质量"
  Output: 结构化 JSON 设计规格
          - 核心循环、控制方案、视觉风格
          - 敌人类型、武器升级、粒子特效
          - UI 布局、反馈系统、难度曲线
  Model:  DeepSeek V4 Flash（强创意）

Step 2: 代码生成（LLM）
  Input:  设计规格 JSON
  Output: 完整 index.html（自包含）
          - Canvas 2D 游戏循环
          - 键盘 + 触摸双控制
          - 粒子效果、屏幕震动、音效
          - 标题画面、暂停、游戏结束
  Model:  DeepSeek V4 Flash（强代码）

Step 3: 代码审查（LLM）
  Input:  游戏代码
  Output: 结构化 JSON 审查报告
          - dimension_a: 工程质量（满分 50）
          - dimension_b: 游戏体验（满分 50）
          - score: 综合评分
          - issues: 问题列表
          - suggestions: 优化建议
  Model:  DeepSeek V4 Flash（强理解）

Step 4: 自动化验证（Playwright）
  Input:  游戏代码
  Output: 测试报告
          - 页面加载无报错
          - Canvas 渲染正常
          - 帧率 ≥ 30fps
          - 控制响应正常
  Tool:   Playwright 无头浏览器

Step 5: 质量决策
  ≥ 80分 → 🏆 精品 → 部署呈现
  60-79分 → 🔄 合格 → 自动优化一轮
  < 60分  → ❌ 不合格 → 告知用户
```

### 3.4 GameEngine API

```json
// 请求
POST /api/v1/game/generate
{
  "prompt": "做一个太空射击小游戏，霓虹风格，精品质量",
  "format": "html5"
}

// 响应
{
  "task_id": "xyz456",
  "status": "completed",
  "score": 85,
  "game_url": "/ghost-content/games/xyz456/index.html",
  "cover_url": "/ghost-content/games/xyz456/cover.png",
  "download_url": "/ghost-content/games/xyz456/game.zip",
  "review": {
    "dimension_a": 42,
    "dimension_b": 43,
    "issues": ["缺少触摸控制"],
    "suggestions": ["添加 touch 事件监听"]
  }
}
```

### 3.5 Gateway 代理路由

新增 `POST /v1/content/game/generate`，代理到 GameEngine 服务：

```python
# ghost-main/gateway/routes/content.py
@router.post("/v1/content/game/generate")
async def generate_game(request: GameGenerateRequest):
    # 1. 验证用户身份
    # 2. 转发到 GameEngine 服务
    # 3. 返回游戏 URL + 评分
    pass
```

---

## 4. 飞书 Bot 集成

### 4.1 新增内容生成命令

```
/video <主题>          — 生成视频
   例：/video 日本赛博朋克城市雨夜，霓虹灯倒映在积水地面

/game <描述>           — 生成游戏
   例：/game 太空射击游戏，霓虹风格，精品质量

/content list          — 查看已生成的内容
/content <id>          — 查看特定内容详情
```

### 4.2 消息处理流程

```
用户发消息
  │
  ▼
bot.py handle_event()
  │
  ├─ 以 / 开头 → _handle_command()
  │   ├─ /video → 调用 MoneyPrinterTurbo API
  │   ├─ /game  → 调用 GameEngine API
  │   └─ /content list → 查询已生成内容列表
  │
  └─ 普通消息 → BackendRunner.run()
      （保留现有行为，不做改动）
```

### 4.3 飞书卡片富媒体

扩展 `feishu_service.py` 的 `_build_card`，支持：

| 卡片类型 | 元素 | 效果 |
|:---------|:-----|:-----|
| **视频卡片** | `tag: "video"` | 聊天窗口内嵌视频播放器 |
| **视频卡片** | `tag: "img"` + action buttons | 封面图 + 播放/下载/分享按钮 |
| **游戏卡片** | `tag: "img"` + `tag: "iframe"` | 封面图 + 游戏直接在聊天窗口运行 |
| **进度卡片** | `tag: "div"` + 进度条 | 生成中显示进度 |

### 4.4 通知流程

```
内容生成完成
  │
  ▼
EventBus.emit("video:generated" / "game:generated", data)
  │
  ▼
FeishuConsumer 消费事件
  │
  ▼
FeishuService.send_card(user_id, title, content, actions)
  │
  ▼
用户收到富卡片通知
```

---

## 5. Ghost DS 前端改造

### 5.1 导航结构调整

当前 Sidebar 四组导航：

| 组 | 当前 | 改为 |
|:--|:-----|:-----|
| 操作区 | 对话, 记忆图谱, 工作流, 运营看板 | 对话, 记忆图谱, 工作流, **内容库** |
| 生态 | 生态总览, A2A 协议, 知识图谱, 社交 | 生态总览, A2A 协议, 知识图谱, 社交 |
| 管理 | 商品管理, 订单管理, 设置 | **商品管理（保留）**, 订单管理（保留）, 设置 |

**"运营看板"→"内容库"**：这是核心变化。内容库是用户生成的所有视频和游戏的展示页。

### 5.2 内容库页面（`/content`）

```
┌──────────────────────────────────────────────────┐
│  内容库                                          │
│  全部  │  视频  │  游戏                            │
├──────────────────────────────────────────────────┤
│                                                  │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐          │
│  │ 🎬 封面  │  │ 🎮 封面  │  │ 🎬 封面  │          │
│  │         │  │         │  │         │          │
│  │ 霓虹太空│  │ 赛博朋克│  │ 日本城市│          │
│  │ 射击    │  │ 番剧    │  │ 雨夜    │          │
│  │         │  │         │  │         │          │
│  │ ⏱ 2:30 │  │ 🏆 85分 │  │ ⏱ 0:45 │          │
│  │ [播放]  │  │ [试玩]  │  │ [播放]  │          │
│  └─────────┘  └─────────┘  └─────────┘          │
│                                                  │
│  ┌─────────┐  ┌─────────┐                       │
│  │ 🎮 封面  │  │ 🎬 封面  │                       │
│  │ ...     │  │ ...     │                       │
│  └─────────┘  └─────────┘                       │
│                                                  │
│           [ 加载更多 ]                            │
└──────────────────────────────────────────────────┘
```

**卡片类型区分：**

| 内容类型 | 卡片样式 | 操作按钮 | 点击行为 |
|:---------|:---------|:---------|:---------|
| **视频** | 封面图 + 时长标签 + 播放按钮 | 播放 / 下载 / 分享 | 新窗口播放或内嵌播放器 |
| **游戏** | 封面图 + 评分标签 + "试玩"按钮 | 试玩（iframe）/ 下载ZIP / 分享 | iframe 内嵌试玩 或 新窗口打开 |

### 5.3 Product 模型扩展

在现有 Prisma schema 上新增字段：

```prisma
model Product {
  # ... 现有字段 ...
  
  contentType  String   @default("product")  // "product" | "video" | "game"
  videoUrl     String?                       // 视频文件路径
  coverUrl     String?                       // 通用封面图
  duration     Int?      @db.Integer         // 视频/游戏时长（秒）
  fileSize     Int?      @db.Integer         // 文件大小（MB）
  
  // 游戏专用
  genre        String?                       // 游戏类型
  platform     String?                       // "Web" | "PC" | "Mobile"
  qualityScore Int?      @db.Integer         // 质量评分（0-100）
  
  // 视频专用
  script       String?   @db.Text            // 生成的脚本文本
  
  rawData      String?   @db.Text            // 保留：存储完整生成元数据
}
```

**注意**：保留现有电商字段（price, inventory, shopId 等），只是新增 contentType 区分。数据库迁移用 `prisma migrate dev`。

### 5.4 Products 页面改造

在 Products 页面的筛选区增加 contentType 过滤：

```typescript
// 筛选栏增加：
<select value={contentType} onChange={...}>
  <option value="all">全部内容</option>
  <option value="product">商品</option>
  <option value="video">视频</option>
  <option value="game">游戏</option>
</select>
```

表格行根据 contentType 显示不同的卡片样式和操作按钮。

---

## 6. 内容存储设计

### 6.1 目录结构

```
/ghost-content/                    ← 内容根目录（可配置）
  ├── videos/
  │   ├── {task_id}.mp4            ← 视频文件
  │   ├── cover_{task_id}.jpg      ← 视频封面
  │   └── script_{task_id}.json    ← 生成脚本记录
  │
  └── games/
      ├── {task_id}/
      │   ├── index.html           ← 自包含游戏文件
      │   ├── cover.png            ← 游戏封面
      │   └── game.zip             ← 打包下载
      └── shared/                  ← 共享游戏资源
```

### 6.2 文件管理 API

| 端点 | 方法 | 功能 |
|:-----|:-----|:-----|
| `/api/content/videos` | GET | 列出所有视频（分页 + contentType 过滤） |
| `/api/content/games` | GET | 列出所有游戏（分页 + 评分过滤） |
| `/api/content/:id` | GET | 单个内容详情 |
| `/api/content/:id/download` | GET | 下载 ZIP（游戏）或 MP4（视频） |
| `/api/content/:id` | DELETE | 删除内容 |
| `/games/:id/` | GET | 静态托管 HTML5 游戏（Next.js 静态文件） |

---

## 7. 完整端到端链路

### 7.1 视频生成链路

```
用户在飞书发："/video 日本赛博朋克城市雨夜"
  │
  ├─ bot.py _handle_command("/video ...")
  │   ├─ 回复"⏳ 正在生成视频，请稍候..."
  │   ├─ POST Gateway /v1/content/video/generate
  │   │   └─ Gateway → MoneyPrinterTurbo :8080
  │   │       ├─ DeepSeek 写脚本
  │   │       ├─ 匹配素材
  │   │       ├─ 生成字幕 + BGM
  │   │       └─ ffmpeg 合成视频
  │   │   └─ 返回 { video_url, cover_url, duration }
  │   ├─ 上传文件到 /ghost-content/videos/{task_id}.mp4
  │   ├─ 写入 Product 数据库记录（contentType="video"）
  │   ├─ EventBus.emit("video:generated", { task_id, ... })
  │   └─ 发送视频卡片到飞书
  │       ├─ 封面图
  │       ├─ Card Video 元素（内嵌播放器）
  │       └─ "查看内容库" 按钮 → Ghost DS /content
  │
  ▼
Feishu Consumer 收到 video:generated 事件
  └─ （可选）额外通知，如"新视频已上架"
```

### 7.2 游戏生成链路

```
用户在飞书发："/game 太空射击游戏，霓虹风格"
  │
  ├─ bot.py _handle_command("/game ...")
  │   ├─ 回复"⏳ 正在设计游戏，请稍候..."
  │   ├─ POST Gateway /v1/content/game/generate
  │   │   └─ Gateway → GameEngine 服务
  │   │       ├─ Step 1: DeepSeek 生成设计规格
  │   │       ├─ Step 2: DeepSeek 生成 HTML5 代码
  │   │       ├─ Step 3: DeepSeek 审查 + 打分
  │   │       ├─ Step 4: Playwright 自动化验证
  │   │       └─ Step 5: 评分决策
  │   │           ├─ ≥ 80分 → 精品 → 部署
  │   │           ├─ 60-79分 → 自动优化一轮
  │   │           └─ < 60分 → 告知用户
  │   ├─ 部署游戏文件到 /ghost-content/games/{task_id}/
  │   ├─ 打包 game.zip
  │   ├─ 写入 Product 数据库记录（contentType="game"）
  │   ├─ EventBus.emit("game:generated", { task_id, score, ... })
  │   └─ 发送游戏卡片到飞书
  │       ├─ 封面图
  │       ├─ Card Iframe 元素（游戏直接跑）
  │       └─ "试玩" 按钮 + "下载" 按钮
  │
  ▼
用户在飞书卡片里直接开始玩
```

---

## 8. 技术栈总览

| 层 | 组件 | 技术 | 状态 |
|:--|:-----|:-----|:-----|
| 输入 | 飞书 Bot | Python + WebSocket/Polling | ✅ 已有 |
| 输入 | Ghost DS | Next.js 14 | ✅ 已有 |
| 视频生成 | MoneyPrinterTurbo | Python + DeepSeek + ffmpeg | ❌ 需部署 |
| 游戏生成 | GameEngine | Python + DeepSeek V4 Flash + Playwright | ❌ 需新建 |
| 内容存储 | 文件系统 + Prisma | /ghost-content/ + PostgreSQL | ❌ 需扩展 |
| 网关 | Gateway | FastAPI | ✅ 已有，需新增路由 |
| 内容展示 | Ghost DS | Next.js + 新页面 | ❌ 需新建 |
| 飞书展示 | FeishuService | 飞书卡片 API | ❌ 需扩展富媒体 |
| 通知 | EventBus | Redis Streams | ✅ 已有 |
| 通知 | FeishuConsumer | Python | ✅ 已有，需新增事件类型 |

---

## 9. 实施阶段

### Phase 1：视频生成通链路（预估 3-5 天）

| 任务 | 改动文件 | 优先级 |
|:-----|:---------|:-------|
| 部署 MoneyPrinterTurbo | Docker compose / 本地 | P0 |
| Gateway 新增视频生成路由 | `gateway/routes/content.py`（新建） | P0 |
| Gateway 配置添加 MPT_URL | `gateway/config.py` | P0 |
| 飞书 Bot 新增 /video 命令 | `feishu-bot/bot.py` | P0 |
| FeishuService 新增视频卡片 | `feishu-bot/feishu_service.py` | P0 |
| DS 内容库 API 路由 | `DS/src/app/api/content/`（新建） | P1 |
| DS 内容库页面 | `DS/src/app/content/page.tsx`（新建） | P1 |
| DS Sidebar 导航更新 | `DS/src/components/layout/Sidebar.tsx` | P1 |
| Product schema 扩展 | `DS/prisma/schema.prisma` | P1 |
| 端到端验证 | 飞书 → 生成 → 卡片 → DS | P0 |

### Phase 2：游戏生成管道（预估 5-7 天）

| 任务 | 改动文件 | 优先级 |
|:-----|:---------|:-------|
| GameEngine 服务 | `ghost-main/game-engine/`（新建） | P0 |
| 5 套 prompt 模板 | `game-engine/prompts/`（新建） | P0 |
| GameEngine API 服务 | `game-engine/main.py`（新建） | P0 |
| Playwright 验证器 | `game-engine/validator.py`（新建） | P0 |
| Gateway 新增游戏生成路由 | `gateway/routes/content.py` | P0 |
| 飞书 Bot 新增 /game 命令 | `feishu-bot/bot.py` | P0 |
| FeishuService 新增游戏卡片（iframe） | `feishu-bot/feishu_service.py` | P0 |
| DS 游戏试玩路由 | `DS/src/app/api/content/` | P1 |
| DS 游戏 iframe 组件 | `DS/src/app/content/` | P1 |
| 端到端验证 | 飞书 → 生成 → 卡片试玩 → DS | P0 |

### Phase 3：品质优化（持续）

| 任务 | 说明 |
|:-----|:-----|
| prompt 迭代 | 根据生成结果持续优化 5 套 prompt |
| 审查标准调优 | 根据实际评分分布调整阈值 |
| 游戏类型模板 | 针对不同游戏类型（射击/平台/解谜）定制设计规格 |
| 视频风格模板 | 针对不同视频风格（动漫/写实/解说）定制 prompt |
| 内容分享 | 生成的内容可分享链接，无需登录即可查看 |
| 打包下载 | 游戏 ZIP、视频 MP4 直接下载 |

---

## 10. 关键设计决策

### D-20260805-1: 视频生成工具选型 MoneyPrinterTurbo

**日期**: 2026-08-05  
**状态**: Proposed  
**背景**: 需要 AI 视频生成能力，市场有多个选项  
**决定**: 选 MoneyPrinterTurbo（免费自部署，完整管道，支持 DeepSeek）  
**理由**: 开箱即用，不需要自己搭脚本/素材/字幕/BGM 管道  
**后果**: 新增一个 Docker 服务 (:8080)，Gateway 新增代理路由

### D-20260805-2: 游戏生成采用 LLM Pipeline 而非专用工具

**日期**: 2026-08-05  
**状态**: Proposed  
**背景**: 市场不存在成熟的 AI 游戏生成 CLI 工具，Unity CLI 是编译器不是生成器  
**决定**: 用 DeepSeek V4 Flash 五步 LLM Pipeline 生成 HTML5 游戏  
**理由**: 游戏代码是文本，LLM 的天生领域；HTML5 输出零摩擦；五步管道保障质量  
**后果**: 新建 ghost-main/game-engine/ 服务，不依赖外部工具

### D-20260805-3: 视频/游戏统一为 "内容" 概念

**日期**: 2026-08-05  
**状态**: Proposed  
**背景**: 视频和游戏是两种不同的内容类型，但共享相同的存储、展示、通知基础设施  
**决定**: 统一为 contentType 字段（"video" | "game" | "product"），同一套 API 路由和前端页面  
**理由**: 减少重复代码，未来可扩展更多内容类型（音频/文章/课程）  
**后果**: Product 模型加 contentType 字段，DS 前端 /content 页面统一展示

### D-20260805-4: 飞书卡片富媒体扩展

**日期**: 2026-08-05  
**状态**: Proposed  
**背景**: 当前飞书卡片只支持 text + action buttons，视频和游戏需要在聊天窗口内直接展示  
**决定**: 扩展 FeishuService._build_card 支持 video 和 iframe 元素  
**理由**: 飞书原生支持 Card Video 和 Iframe 元素，用户体验远优于转发链接  
**后果**: feishu_service.py 新增 send_video_card / send_game_card 方法

### D-20260805-5: 游戏质量五步管道

**日期**: 2026-08-05  
**状态**: Proposed  
**背景**: 用户要求"高质量精品"产出，单次 LLM 生成不够稳定  
**决定**: 设计规格 → 代码生成 → AI 审查 → Playwright 验证 → 评分决策  
**理由**: 多步管道将生成质量从"碰运气"提升到"可控标准"  
**后果**: 每个游戏生成需要 3-5 次 LLM API 调用 + 1 次 Playwright 测试，耗时约 30-60 秒

---

## 11. 待确认事项

- [ ] MoneyPrinterTurbo 部署在哪台机器上？需要 GPU 吗？
- [ ] DeepSeek V4 Flash 的 API endpoint 和 key 是否已就绪？
- [ ] Playwright 是否可以在现有 Docker 环境中运行（需要 Chromium）？
- [ ] /ghost-content/ 目录是否需要定期清理（磁盘空间管理）？
- [ ] 视频生成失败时的降级策略（回退到纯脚本展示）？

---

*本文档为 Ghost Platform 内容生成管道的完整设计方案。*
