# Ghost Phase 1 可执行实施方案 · Implementation Pack v0.1

> 本文档只做一件事：把 Phase 1 最小闭环落到具体角色、端点、脚本和验证命令上。
> 严格遵循前面已冻结的边界：只做 A2A 治理最小链，不建 second skill、不新增前端、不做市场。

---

## 1. 角色扮演（固定）

- **Agent A（用户代表）**
  - 身份来源：用户通过 Gateway 触发
  - 职责：提出任务、查看结果、查看审计、查看记忆
- **Agent B（执行者）**
  - 身份来源：平台内一个已注册的 A2A Agent
  - 职责：暴露唯一 skill，接受调用，返回结果

演示时：
- Agent A 是“用户视角”
- Agent B 是“被治理的工具执行者”

---

## 2. 唯一外部 Skill 选型

**选定：公开 HTTP JSON API，无需 key，稳定可演示**
- 先做 **1 个 skill：搜索/查询类**
- 示例外部 skill：
  - https://jsonplaceholder.typicode.com/posts/1
  - 或任意固定返回 JSON 的公开接口

选型理由：
- 不需要真实 API key
- 不需要额外注册
- 只用来证明“外部 skill 调用被 Ghost 治理”

---

## 3. Ghost 侧最小 skill 定义

用 1 个固定 skill 做样本：

`json
{
  "skill_id": "ghost.sample.fetch",
  "name": "Fetch Sample JSON",
  "description": "Get a fixed sample JSON result for demo.",
  "parameters": {
    "type": "object",
    "properties": {
      "endpoint": {
        "type": "string",
        "enum": ["https://jsonplaceholder.typicode.com/posts/1"]
      }
    },
    "required": ["endpoint"]
  }
}
`

Claude 只返回：
- status
- body summary
- audit trace id
- memory write index

---

## 4. 最小端点清单（6 个）

### Alpha-ID
- POST /api/v1/a2a/register
- POST /api/v1/a2a/discover
- POST /api/v1/a2a/call

### Gateway
- POST /v1/agent/a2a/call
- GET  /v1/agent/a2a/audit

### 记忆
- POST /api/v1/dual-chain/save
- GET  /api/v1/dual-chain/stats

> 注意：这里列出 7 个端点，但对外演示只看 6 步主链。

---

## 5. 6 步最小调用链

`
1. 用户任务
    -> Gateway

2. Gateway 取当前 Agent 身份
    -> Alpha-ID

3. A2A Runtime 查询目标 Agent 能力与授权
    -> register / discover

4. Ghost Agent 发起外部 skill 调用
    -> call

5. 写审计日志
    -> audit

6. 结果回写双链记忆
    -> dual-chain/save
`

演示时只讲这条链，不展开其他模块。

---

## 6. 5 分钟演示脚本

### 第一部分：30 秒，讲定位
- Ghost 不是聊天壳
- Ghost 是 A2A Agent 的治理运行时
- 模型和 skill 会越来越强，但“谁调用、为什么调用、结果如何”仍然需要治理层

### 第二部分：2 分钟，注册与发现
`ash
# 1 注册 Agent B（执行者）
curl -X POST http://localhost:18080/v1/agent/a2a/register \
  -H "Content-Type: application/json" \
  -d '{
    "agent_id": "agent-b-001",
    "public_key": "example_public_key",
    "skill_list": ["ghost.sample.fetch"],
    "permission_scope": ["call:ghost.sample.fetch"],
    "call_constraint": {"max_per_min": 10},
    "memory_policy": "write_summary"
  }'

# 2 发现 Agent B
curl -X POST http://localhost:18080/v1/agent/a2a/discover \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "agent-b-001"}'
`

### 第三部分：2 分钟，调用与治理
`ash
# 3 发起一次受治理的调用
curl -X POST http://localhost:18080/v1/agent/a2a/call \
  -H "Content-Type: application/json" \
  -d '{
    "caller_agent_id": "agent-a-001",
    "target_agent_id": "agent-b-001",
    "skill": "ghost.sample.fetch",
    "params": {
      "endpoint": "https://jsonplaceholder.typicode.com/posts/1"
    },
    "auth": {
      "grant_type": "temporary",
      "scope": ["call:ghost.sample.fetch"],
      "expire_at": "2026-08-04T00:00:00Z"
    },
    "signature": "demo_signature_hex"
  }'
`

### 第四部分：1 分钟，查看审计与记忆
`ash
# 4 查看审计
curl "http://localhost:18080/v1/agent/a2a/audit?caller=agent-a-001"

# 5 查看记忆统计
curl "http://localhost:8000/api/v1/dual-chain/stats"
`

---

## 7. 4 个必需验证命令

`ash
# 验证 1：Alpha-ID 健康
curl -s http://localhost:8000/health

# 验证 2：Gateway 健康
curl -s http://localhost:18080/health

# 验证 3：调一次最小 A2A 调用
curl -s -X POST http://localhost:18080/v1/agent/a2a/call \
  -H "Content-Type: application/json" \
  -d '{"caller_agent_id":"agent-a-001","target_agent_id":"agent-b-001","skill":"ghost.sample.fetch","params":{"endpoint":"https://jsonplaceholder.typicode.com/posts/1"},"auth":{"grant_type":"temporary","scope":["call:ghost.sample.fetch"],"expire_at":"2026-08-04T00:00:00Z"},"signature":"demo_signature_hex"}'

# 验证 4：审计和记忆两头都能查到
curl -s "http://localhost:18080/v1/agent/a2a/audit?caller=agent-a-001"
curl -s "http://localhost:8000/api/v1/dual-chain/stats"
`

---

## 8. 明确禁止边界（执行期铁律）

**禁止：**
- 不新增前端页面
- 不加第二个外部 skill
- 不做多租户
- 不做计费
- 不做市场
- 不碰 Ghost.html 功能扩展
- 不碰 MindFlow/NURO/豆包/Net-Agent/Orchestrator 主线开发
- 不重构非主链模块

**允许：**
- 只改 Phase 1 最小链必要文件
- 只加必要注释
- 只做可演示的最小逻辑

---

## 9. 先改的 5 个文件

1. lphaid/projects/src/core/a2a.py
2. lphaid/projects/src/main.py
3. ghost-main/gateway/routes/agent.py
4. lphaid/projects/src/core/observability.py
5. lphaid/projects/src/api/dual_chain.py

---

## 10. 验收标准（最终版）

不是“功能很多”，而是：

> **5 分钟内可演示：**
> **“Ghost Agent 有身份、可发现、调用一个外部 skill、有签名、有审计、结果被写回记忆。”**

这个 demo 足以拿去面试，也足以说明你做的不是一个前端聊天壳。
