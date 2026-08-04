Phase 1 实施计划已清晰：

P0（代码 + 项目管理基础设施）：
1. 合并两个 Python MasterOrchestrator → OrchestratorEngine
2. EventBus blinker → Redis Streams
3. 修复 /v1/chat 断裂链路
4. 激活 Redis Streams 消费
5. 创建根 Makefile（统一 up/test/lint 命令）
6. 将 Ghost DS 加入 CI
7. 创建 AGENTS.md（项目级 AI 指令）
8. 创建 CODEOWNERS（代码归属）
9. 创建 CONTRIBUTING.md（贡献规范）

P1：盘活死代码（wechat + eventbus-server 合并）

P2：ToolA/ToolB stub → 真实接入、术语注释标准化

执行顺序：先写 PHASE1_PLAN.md 文件并 git commit，然后按 P0→P1→P2 逐个实施。