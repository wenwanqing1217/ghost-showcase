# MindFlow Blocks - Interview Demo

本目录用于整理 `mindflow`、`ai综艺`、`zcode-brain` 三个块的面试演示顺序和验收口径。

## 推荐演示顺序

1. `zcode-brain`：先跑 `npm test`，说明任务如何匹配到专家角色，以及安全护栏如何先行。
2. `mindflow`：展示可运行的 Web + API，说明测试、构建、部署都已就绪。
3. `ai综艺`：展示构建产物和交互效果，说明前端体验和动画已完成生产化验证。

## 快速命令

```bash
# 1. 检查构建与测试
cmd /c "build-all.bat <NUL"
node demo/verify.js

# 2. ZCode Brain 角色匹配
cd zcode-brain
npm test

# 3. MindFlow 全栈演示
cd mindflow
npm run dev

# 4. ai综艺 演示
cd "ai综艺"
npm run dev
```

## 当前验证结果

- `zcode-brain`：`10/10` passed
- `mindflow`：构建通过，`32/32` passed（API 16 + Web 11 + Shared 5）
- `ai综艺`：构建通过，产物已生成
