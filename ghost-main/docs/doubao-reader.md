# 豆包知识管道 (Doubao Reader)

> **版本**: 1.0  
> **日期**: 2026-07-27  
> **位置**: `ghost-main/doubao_reader/`  
> **规模**: 1,055 行 / 5 文件  
> **状态**: ✅ 已完成，Gateway 已接入

---

## 1. 定位

豆包知识管道是 Ghost 项目 **Pipeline A（知识进）** 的核心组件，负责将豆包桌面 App 本地 LevelDB 存储的对话记录自动扫描、精炼、沉淀到 Obsidian 知识库，并通过 Gateway 统一网关与 Alpha-ID 身份层联动。

**核心价值**：将碎片化 AI 对话转化为结构化个人知识资产。

---

## 2. 模块结构

| 文件 | 行数 | 职责 |
|------|------|------|
| `log_reader.py` | 239 | LevelDB 解析器，提取 ChatMessage/Conversation |
| `knowledge_refiner.py` | 204 | 噪声过滤 + 关键词标签映射 + 规则化 NLP |
| `obsidian_writer.py` | 208 | YAML frontmatter 生成 + Gateway 轮询 + .md 写入 |
| `obsidian_organizer.py` | 306 | wiki-links 构建 + 日报汇总 + 标签索引 + 交叉引用 |
| `reader_daemon.py` | 98 | 后台守护进程，60s 间隔轮询 |

---

## 3. 数据流

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────┐
│ 豆包桌面 App │────▶│  log_reader  │────▶│ knowledge_refiner │
│  LevelDB    │     │  (解析对话)   │     │  (噪声过滤+标签)   │
└─────────────┘     └──────────────┘     └────────┬─────────┘
                                                   │
                                                   ▼
┌─────────────┐     ┌──────────────┐     ┌──────────────────┐
│  Obsidian   │◀────│ obsidian_    │◀────│  obsidian_writer  │
│  .md 知识库  │     │ organizer    │     │  (YAML+写入)      │
└─────────────┘     └──────────────┘     └──────────────────┘
                                                   │
                                                   ▼
                                          ┌──────────────────┐
                                          │  Gateway          │
                                          │  /v1/internal/    │
                                          │  doubao/capture   │
                                          └──────────────────┘
```

---

## 4. 模块详解

### 4.1 log_reader.py — LevelDB 解析器

- 解析豆包桌面 App 本地 LevelDB 存储
- 提取结构化数据：`ChatMessage`（单条消息）+ `Conversation`（完整对话）
- 支持增量扫描，避免重复处理

### 4.2 knowledge_refiner.py — 知识精炼器

- **噪声过滤规则**：过滤系统消息、空内容、重复对话、过短消息
- **关键词→标签映射**：内置关键词表，自动为对话打标签
- **规则化 NLP**：基于规则的轻量级自然语言处理（无需外部模型）

### 4.3 obsidian_writer.py — Obsidian 写入器

- 生成标准 YAML frontmatter（title, tags, date, source）
- 轮询 Gateway 获取用户身份信息
- 按日期/标签目录结构写入 `.md` 文件

### 4.4 obsidian_organizer.py — 自动整理器

- **wiki-links 构建**：自动识别对话中的实体并生成 `[[实体名]]` 链接
- **日报汇总**：按天聚合对话，生成每日知识摘要
- **标签索引**：维护标签→文档的反向索引
- **交叉引用**：发现对话间的关联并自动链接

### 4.5 reader_daemon.py — 后台守护进程

- `DaemState` 状态机管理运行状态
- 默认 60 秒轮询间隔
- 调用 Gateway `POST /v1/internal/doubao/capture` 推送精炼结果

---

## 5. Gateway 集成

### 5.1 端点

```
POST /v1/internal/doubao/capture
```

### 5.2 安全限制

- **IP 限制**: 仅允许 `localhost` 访问（内部管道）
- 请求体需包含 `session_id` + `messages` 字段

### 5.3 处理流程

1. 接收豆包精炼后的对话数据
2. 调用 `knowledge_refiner.refine_conversation()` 二次精炼
3. 验证 `session_id` 与 `messages` 完整性
4. 返回处理结果供 Obsidian 写入器使用

---

## 6. Obsidian 输出格式

### 6.1 YAML Frontmatter

```yaml
---
title: "对话标题"
tags: [AI, 豆包, 自动标签1, 自动标签2]
date: 2026-07-27
source: doubao-leveldb
session_id: "abc123"
---
```

### 6.2 目录结构

```
vault/
├── daily/
│   └── 2026-07-27.md          # 日报汇总
├── tags/
│   ├── AI.md                   # 标签索引
│   └── 编程.md
├── conversations/
│   └── 2026-07-27-会话标题.md  # 单篇对话
└── index.md                    # 总索引
```

---

## 7. 配置与运行

### 7.1 依赖

```
leveldb
pyyaml
requests
```

### 7.2 启动守护进程

```bash
cd ghost-main/doubao_reader
python reader_daemon.py
```

### 7.3 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `DOUBAO_LEVELDB_PATH` | 豆包 LevelDB 路径 | `~/.doubao/leveldb` |
| `GATEWAY_URL` | Gateway 地址 | `http://localhost:8080` |
| `POLL_INTERVAL` | 轮询间隔（秒） | `60` |
| `OBSIDIAN_VAULT_PATH` | Obsidian vault 路径 | `./vault` |

---

## 8. 噪声过滤规则

| 规则 | 说明 |
|------|------|
| 系统消息 | 过滤 `[SYSTEM]` 前缀消息 |
| 空内容 | 过滤空字符串或纯空白 |
| 过短消息 | 过滤 < 10 字符的消息 |
| 重复对话 | 基于内容哈希去重 |
| 无效 JSON | 跳过解析失败的记录 |

---

## 9. 开发笔记

### 9.1 扩展点

- **新增标签映射**: 修改 `knowledge_refiner.py` 的关键词表
- **自定义输出格式**: 扩展 `obsidian_writer.py` 的 frontmatter 模板
- **调整轮询频率**: 修改 `reader_daemon.py` 的 `POLL_INTERVAL`

### 9.2 已知限制

- 仅支持豆包桌面 App 的 LevelDB 格式
- 噪声过滤为规则化方案，不支持 ML 模型
- 单线程处理，大量对话时可能有延迟

### 9.3 后续规划

- [ ] 支持更多 AI 对话源（ChatGPT、Claude 等）
- [ ] 引入 LLM 辅助精炼（替代纯规则方案）
- [ ] 增量索引优化（大规模 vault 性能）

---

## 10. 关联文档

- [GHOST.md](../../GHOST.md) — 项目总览
- [Gateway API](../../../alphaid/projects/docs/) — Gateway 路由文档
- [NURO 桌面精灵](../../../alphaid/projects/docs/nuro-desktop-pet.md) — Pipeline D 组件
