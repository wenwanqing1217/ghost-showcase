# Ghost Phase 1 面试演示脚本 · Demo Script v0.1

> 用途：5 分钟讲清楚 Ghost 是什么、不是做什么、以及最小可信闭环怎么演示。  
> 前置：已按 PHASE1_IMPLEMENTATION_PACK.md 把最小链跑通。

---

## 1. 开场（30 秒）

> “现在很多项目都在做更漂亮的聊天前端、更强的模型调用、更大的 Agent 生态。
> 但我觉得真正缺的不是这些，而是 Agent 的治理层。
> 所以 Ghost 不是一个聊天壳，而是一个 A2A Agent 的治理运行时。”

---

## 2. 定位一句话（30 秒）

**对外只说：**
> “Ghost 让你的 Agent 有身份、能被授权、能调用能力、能留下审计、而且记忆属于你。”

**明确边界：**
- 不做第二聊天前端
- 不做工具市场
- 不做多租户 SaaS

---

## 3. 当前阶段（30 秒）

> “现在先做 Phase 1：把最小可信闭环跑通。”
> 核心链路：身份 -> 发现 -> 授权 -> 调用 -> 审计 -> 记忆回写

---

## 4. 演示脚本（3 分钟）

### Step 1：健康检查
`ash
curl -s http://localhost:8000/health
curl -s http://localhost:18080/health
`

### Step 2：注册 Agent B
`ash
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
`

### Step 3：发现 Agent B
`ash
curl -X POST http://localhost:18080/v1/agent/a2a/discover \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "agent-b-001"}'
`

### Step 4：受治理调用
`ash
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

### Step 5：查看审计
`ash
curl -s "http://localhost:18080/v1/agent/a2a/audit?caller=agent-a-001"
`

### Step 6：查看记忆
`ash
curl -s "http://localhost:8000/api/v1/dual-chain/stats"
`

---

## 5. 解释话术（1 分钟）

- **身份层**：每个 Agent 有独立身份和公钥
- **发现层**：支持能力发现，不靠死配置
- **治理层**：调用前有最小授权，调用后有审计
- **记忆层**：结果会回写，且不依赖单一平台记忆
- **差异化**：模型和 skill 都会越来越强，但“可信调用与记忆主权”仍需单独治理

---

## 6. 常见问题速答

**Q：为什么不直接用 MCP / Codex / LangChain？**
- 它们很好，但更偏工具/前端/执行体验。
- Ghost 补的是**身份归属、授权边界、审计和用户主权记忆**。

**Q：记忆不是模型上下文记忆就够了吗？**
- 不够，因为平台记忆不是用户可携带资产。
- Ghost 记忆强调**用户可带走、可授权、可撤销、可审计**。

**Q：这不是又做了一套抽象层吗？**
- 如果只是转发调用，就是多余的。
- 但如果负责**委托治理、权限、审计、记忆回写**，就形成不可替代层。

---

## 7. 收尾（30 秒）

> “Ghost 下一步不是做更多前端或更多 skill，
> 而是把这个治理层做成可嵌入其他工具的基础设施。”

建议收尾展示：
- 一个已经跑通的 registry/call/audit/memory demo
- 一句明确的产品边界
- 一句明确的下一步：先可运行，再做开放 SDK
