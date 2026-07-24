# Ghost Dual-Chain Memory — Obsidian Plugin

双向同步 Obsidian 笔记与 Ghost 双链记忆系统。

## 功能

- ⬆ **上传笔记**：Obsidian markdown → Ghost 知识链/私有链
- ⬇ **下载记忆**：Ghost 知识链 → Obsidian markdown
- 🔄 **双向同步**：按时间戳检测冲突，自动合并
- 🔐 **敏感度控制**：frontmatter `sensitivity` 字段决定链归属（70+ 进入私有链）
- ⏱ **自动同步**：可配置间隔，后台静默同步

## 安装

1. 复制 `obsidian-plugin/` 到你的 Vault 的 `.obsidian/plugins/ghost-dual-chain/`
2. 在 Obsidian 设置 → 第三方插件中启用「Ghost Dual-Chain Memory」
3. 配置 API 地址（默认 `http://localhost:8000`）

## 使用

### 手动同步
- 点击 Ribbon 的刷新图标
- 或命令面板：`Ghost 双链记忆同步: 立即同步`

### 笔记格式
在 Obsidian 笔记的 frontmatter 中指定敏感度：

```yaml
---
sensitivity: 85    # 70+ 进入私有链（加密存储）
category: secret
tags: [密码, 私钥]
---
```

### 自动同步
在设置中开启「自动同步」并配置间隔（默认 30 分钟）。

## API 依赖

需要 Ghost AlphaID 服务运行在配置的 API 地址。
启动命令：

```bash
cd alphaid/projects
python -m src.entrypoints.api --port 8000
```

## 文件结构

```
obsidian-plugin/
  manifest.json      — 插件清单
  main.ts            — 插件入口 + Ribbon/命令
  styles.css         — 状态栏样式
  src/
    settings.ts      — 设置页面 + 配置接口
    sync.ts          — 核心同步逻辑
    api.ts           — Ghost API 客户端
    types.ts         — 共享类型
  README.md          — 本文档
```
