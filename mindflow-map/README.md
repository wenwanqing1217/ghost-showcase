# MindFlow Map

**MindFlow Map - AI 统一工作流引擎 | 飞书/微信/公众号多端接入 | 百度地图 Agent Plan | 抖音短剧自动化 | Shopify 电商运营**

一句话：你在飞书/微信里说话，MindFlow 自动帮你查地图、规划路线、发短剧、运营店铺，所有平台统一在一个工作台里。

---

## 面试演示要点

### 项目亮点
- **真实集成，非 Demo 数据**：百度地图 Agent Plan API 已联通，飞书长连接已跑通，Workspace 前后端已联调
- **多端统一入口**：飞书 / 微信 / Workspace 共用同一工作流引擎，一套逻辑多端响应
- **AI 原生架构**：意图识别 → 工具编排 → 多线程执行 → 统一回复，完整 AI 应用链路
- **最小可行产品**：核心路径已打通，剩余模块为框架级实现，可快速接入真实 API

### 模块演示清单

| 模块 | 状态 | 演示方式 |
|------|------|----------|
| 飞书机器人 | 生产可用 | 长连接模式，无需公网 IP，消息实时收发 |
| 百度地图 | 生产可用 | Agent Plan API，语义化地点检索、路线规划、天气 |
| MindFlow Workspace | 可用 | 统一工作台，集成地图、书签、聊天、短剧、电商 |
| 工作流引擎 | 可用 | 意图识别 + 多线程执行 + 工具编排 |
| 微信公众号 | 已实现 | Webhook 适配器已就位，可接入 Server 模式 |
| 抖音自动化 | 可演示 | Playwright 自动化框架已搭建 |
| Shopify 运营 | 可演示 | Admin API 客户端已对接 |

## 快速开始

```bash
# 1. 克隆项目
git clone <repo-url>
cd mindflow-map

# 2. 安装依赖
pip install -e .
playwright install chromium

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，填入 BAIDU_MAP_AUTH_TOKEN 和飞书凭证

# 4. 启动服务（Windows）
scripts\start.bat

# 或 Linux/macOS
bash scripts/start.sh

# 5. 访问
# Workspace: http://localhost:8000/workspace
# API 文档: http://localhost:8000/docs
# 健康检查: http://localhost:8000/health
```

## 项目结构

```
mindflow-map/
├── src/mindflow_map/
│   ├── main.py              # FastAPI 入口 + 飞书长连接启动
│   ├── config.py            # 配置管理（绝对路径 .env）
│   ├── api/                 # API 路由
│   │   ├── feishu.py        # 飞书长连接客户端
│   │   ├── feishu_sender.py # 飞书消息发送
│   │   ├── wechat.py        # 微信 Webhook 适配器
│   │   ├── map.py           # 地图 API
│   │   └── workflow.py      # 工作流 API
│   ├── workflows/           # 工作流引擎
│   │   └── engine.py        # 意图识别 + 线程池 + 工具编排
│   ├── tools/               # 工具集成
│   │   └── baidu_map.py     # 百度地图 Agent Plan SDK
│   ├── automation/          # 自动化
│   │   ├── douyin.py        # 抖音 Playwright 自动化
│   │   └── shopify.py       # Shopify Admin API
│   ├── identity/            # 身份层
│   │   └── aid_client.py    # Alpha-ID 客户端
│   └── memory/              # 记忆层
│       └── store.py         # SQLite 存储
├── static/                  # Workspace 前端资源
├── templates/               # Workspace HTML
├── tests/                   # 测试
├── docs/                    # 文档
├── scripts/                 # 启动脚本
├── pyproject.toml
└── README.md
```

## 面试演示脚本（5分钟版）

### 演示前检查清单
- [ ] 后端服务运行中：`http://localhost:8000/health` 返回 `ok`
- [ ] Workspace 可访问：`http://localhost:8000/workspace`
- [ ] API 文档可用：`http://localhost:8000/docs`
- [ ] 飞书机器人已连接（长连接模式）

### 演示步骤
1. **打开 Workspace**：`http://localhost:8000/workspace`，展示统一工作台界面
2. **地图查询**：在「地图助理」输入「中关村」，展示真实地点搜索结果
3. **路线规划**：输入起点「中关村」、终点「故宫」，展示路线规划结果
4. **AI 对话**：切换到「AI 对话」，输入「怎么去天安门」，展示意图识别 + 路线规划
5. **飞书入口**：展示飞书长连接已启动，手机端可发消息触发同一工作流
6. **后台 API**：打开 `http://localhost:8000/docs`，展示 RESTful API 文档

## 核心流程

```
用户消息（飞书 / 微信 / Workspace）
    ↓
FastAPI 主入口
    ↓
工作流引擎（ThreadPoolExecutor 8 线程）
    ├── 意图识别（地点搜索 / 导航 / 短剧 / 电商）
    ├── 并行执行（用户上下文 + 意图解析）
    └── 工具调用
        ├── 百度地图 Agent Plan（地点 / 路线 / 天气）
        ├── 抖音 Playwright（短剧发布）
        └── Shopify Admin API（商品 / 订单）
    ↓
统一回复（飞书 / 微信 / Workspace）
```

### 真实集成说明

| 集成 | 实现方式 | 状态 |
|------|----------|------|
| 百度地图 | Agent Plan API，Bearer Token 鉴权 | 已联通，返回真实数据 |
| 飞书 | lark-oapi SDK 长连接模式 | 已跑通，消息实时收发 |
| 微信公众号 | XML Webhook 适配器 | 已实现：签名验证 + Access Token 缓存 + 文本消息自动回复 |
| 抖音 | Playwright 浏览器自动化 | 框架已搭建，可接入官方 API |
| Shopify | Admin API REST 客户端 | 框架已对接，可接入真实店铺 |

## 技术栈

| 组件 | 技术 |
|------|------|
| 后端 | Python FastAPI + Uvicorn |
| AI | DeepSeek / 豆包 API（可插拔） |
| 地图 | 百度地图 Agent Plan（Bearer Token） |
| 自动化 | Playwright（抖音短剧） |
| 电商 | Shopify Admin API |
| 前端 | 原生 HTML/CSS/JS，Tailwind CSS |
| 数据库 | SQLite + SQLAlchemy（记忆存储） |
| 部署 | 任意支持 Python 的服务器 |

## 成本

| 服务 | 费用 |
|------|------|
| 飞书机器人 | 永久免费 |
| 百度地图 | 30万次/天 免费 |
| DeepSeek API | 新用户送 5000万 token |
| 部署 | 0元（本地 / 免费额度） |

## 路线图

- [x] Phase 1: 基础架构 + 飞书长连接
- [x] Phase 2: 百度地图 Agent Plan 集成
- [x] Phase 3: MindFlow Workspace 统一工作台
- [x] Phase 4: 微信公众号接入（Webhook 适配器已实现）
- [ ] Phase 5: 抖音短剧全自动化
- [ ] Phase 6: Shopify 深度运营

## License

MIT
