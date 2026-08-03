# Ghost Phase 1 最小开工任务书 v0.1

> 本文档只回答一件事：**接下来用什么最小可行路径，真正把 Phase 1 跑起来。**
> 它不考虑理想形态，只考虑“现在就能执行的下一步”。

---

## 0. 唯一目标

2-4 周内，交付一个可运行的最小 A2A 可信治理样本，满足：

> Ghost Agent 拥有身份 → 能发现另一 Agent → 调用一个外部 Skill → 留下审计记录 → 回写记忆。

不做多租户、不做市场、不做第二前端、不做第二个 Skill。
先把这一条链打通，再做后续。

---

## 1. 当前冻结范围

**只保留**：
- Alpha-ID
- Gateway
- A2A Runtime

**现阶段冻结**：
- Ghost.html 新增页面
- MindFlow、NURO、豆包、Net-Agent、Orchestrator 新功能接入
- 多租户、计费、生态市场

---

## 2. 唯一外部 Skill 样本

先只接 **1 个外部 Skill**，用于证明“工具调用可被身份/授权/审计包裹”。

建议优先级：
1. 代码执行 / shell（如果已有稳定后端）
2. 搜索
3. 地图 POI（你已有雏形）

第一阶段只选 1 个。
选好后，所有调用都只走这一个 Skill。

---

## 3. 最小调用链（固定为 6 步）

`
用户发出任务
  → Ghost Gateway 校验身份
    → Alpha-ID 返回当前 Agent 身份
      → A2A Runtime 查目标 Agent 的 skill 与授权
        → 调用外部 Skill
          → 写审计日志
            → 结果回写双链记忆
`

只要这 6 步能一次跑通，Phase 1 就算成立。

---

## 4. 最小端点设计（先只做这些）

### Alpha-ID / A2A
- POST /api/v1/a2a/register
- POST /api/v1/a2a/discover
- POST /api/v1/a2a/call

### Gateway
- POST /v1/agent/a2a/call
- GET /v1/agent/a2a/audit

### 审计与记忆
- 审计写入 core/observability 或新增简单结构化日志
- 调用结果写回现有 dual_chain 记忆

---

## 5. 先从哪 3-5 个文件动手

优先修改：
1. lphaid/projects/src/core/a2a.py
2. lphaid/projects/src/main.py
3. ghost-main/gateway/routes/agent.py
4. lphaid/projects/src/core/observability.py
5. lphaid/projects/src/api/dual_chain.py

目标是：
- registry/discover 落地
- skill 调用新增一个真实外部 skill
- audit 字段收敛为固定 schema
- 结果写回双链记忆

---

## 6. 5 分钟验收脚本（示例思路）

`ash
# 1. 启动 Alpha-ID
python -m uvicorn alphaid.projects.src.main:app --port 8000

# 2. 启动 Gateway
python -m uvicorn ghost-main.gateway.app:app --port 18080

# 3. 注册 Agent A
curl -X POST http://localhost:18080/v1/agent/a2a/register ...

# 4. Agent B 发现 Agent A
curl -X POST http://localhost:18080/v1/agent/a2a/discover ...

# 5. 发起一次 skill 调用
curl -X POST http://localhost:18080/v1/agent/a2a/call ...

# 6. 查看审计
curl http://localhost:18080/v1/agent/a2a/audit ...

# 7. 查看记忆
curl http://localhost:8000/api/v1/dual-chain/stats ...
`

实际命令以最终实现为准，但验收逻辑必须是：
> 一次调用，处处可查。

---

## 7. 你现在唯一需要回答的问题

在动手前，请先选定：

1. **第一个外部 Skill 是谁**
2. **第一个演示任务是什么**
3. **谁来扮演 Agent A / Agent B**

有了这三个答案，这版任务书就可以变成真正的开发任务拆解。

---

## 8. 后续原则

- 先跑通一条链
- 再抽象规则
- 再做工具化
- 不要反过来

---

*本文件为最小执行版，后续所有优化均应建立在 Phase 1 最小闭环跑通之后。*
