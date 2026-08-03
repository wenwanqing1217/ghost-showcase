# GPU Task Scheduler — 云端 GPU 资源调度系统

> 一个模拟 Kubernetes GPU 调度策略的任务调度系统，支持优先级调度、公平分享、MIG 切分、GPU 监控。
> 
> **项目定位**：面试顺天创（云上算力）的后端开发岗 / FDE 岗的作品集项目

---

## 🎯 项目亮点

| 特性 | 技术点 | 面试可聊 |
|:---|:---|:---|
| 多策略调度器 | 策略模式 + 工厂模式 | 调度算法设计 |
| GPU 资源模型 | 显存/算力/MIG 切分 | GPU 调度原理 |
| 任务队列 | 优先级队列 + 公平分享 | 多租户资源分配 |
| RESTful API | FastAPI + JWT 认证 | 后端 API 设计 |
| 监控指标 | Prometheus + Grafana | 可观测性 |
| 容器化 | Docker Compose | DevOps |
| Web 前端 | 简洁的任务提交/监控页面 | 全栈能力 |

---

## 🏗️ 架构

```
┌─────────────────────────────────────────────────────────────┐
│                     前端 (简易 Dashboard)                    │
│                     任务提交 / 状态监控                      │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP / WebSocket
┌──────────────────────────▼──────────────────────────────────┐
│                   API Gateway (FastAPI)                      │
│  /auth/*  /jobs/*  /nodes/*  /metrics  /ws/*                │
│  JWT 认证 | 限流 | 信封响应                                  │
└──────────┬─────────────────────────────────┬────────────────┘
           │                                 │
┌──────────▼──────────┐      ┌───────────────▼────────────────┐
│   Scheduler 调度器   │      │   Monitor 监控模块              │
│   - FIFO            │      │   - GPU 利用率采集              │
│   - Priority        │      │   - 任务状态跟踪                │
│   - Fair Share      │      │   - Prometheus 指标             │
│   - MIG Aware       │      │   - 告警规则                    │
└──────────┬──────────┘      └────────────────────────────────┘
           │
┌──────────▼──────────────────────────────────────────────────┐
│                    GPU 节点池                                 │
│  Node-A: A100-80GB × 4 (可切分 MIG)                         │
│  Node-B: A100-40GB × 2                                       │
│  Node-C: V100-32GB × 4                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 快速启动

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动（模拟模式，不需要真实 GPU）
python -m api.main

# 3. 或者 Docker 一键启动
docker compose up -d

# 4. 访问
# API 文档: http://localhost:8000/docs
# Dashboard: http://localhost:8000
# Prometheus: http://localhost:9090
```

---

## 📡 API 概览

| 方法 | 路径 | 说明 |
|:---|:---|:---|
| POST | `/auth/register` | 用户注册 |
| POST | `/auth/login` | 登录获取 JWT |
| POST | `/jobs` | 提交 GPU 任务 |
| GET | `/jobs` | 查看任务列表 |
| GET | `/jobs/{id}` | 查看任务详情 |
| DELETE | `/jobs/{id}` | 取消任务 |
| GET | `/nodes` | 查看 GPU 节点状态 |
| GET | `/nodes/{id}` | 查看节点详情 |
| GET | `/metrics` | Prometheus 指标 |
| WS | `/ws/jobs` | WebSocket 实时推送任务状态 |

---

## 🎬 面试话术

> "为了准备这次面试，我做了一个 GPU 任务调度系统——模拟顺天创云上算力的核心调度逻辑。
> 
> 它实现了四种调度策略（FIFO、优先级、公平分享、MIG 感知），支持 GPU 资源的申请/释放/切分，还有 Prometheus 监控。
> 
> 这个项目让我深入理解了 GPU 云平台的核心挑战：资源碎片、多租户隔离、调度公平性。"

---

## 📁 项目结构

```
gpu-scheduler/
├── api/                    # FastAPI 后端
│   ├── main.py            # 入口
│   ├── routes/            # 路由
│   └── middleware/        # 中间件
├── scheduler/             # 调度器核心
│   ├── scheduler.py       # 调度器主逻辑
│   ├── strategies.py      # 调度策略
│   └── gpu_pool.py        # GPU 节点池
├── models/                # 数据模型
│   ├── job.py             # 任务模型
│   ├── node.py            # 节点模型
│   └── user.py            # 用户模型
├── monitor/               # 监控模块
│   ├── collector.py       # 指标采集
│   └── alerts.py          # 告警
├── frontend/              # 简易前端
├── tests/                 # 测试
├── docker-compose.yml
├── Dockerfile
└── requirements.txt
```
