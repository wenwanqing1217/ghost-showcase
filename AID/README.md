# Alpha-ID - 数字身份基础设施

> Alpha-ID 是 MindFlow 统一平台的 **数字身份层**，提供 DID、记忆、Ghost Layer 和 I2I 协议。

## MindFlow 品牌生态

| 项目 | 定位 | 仓库 |
|------|------|------|
| [MindFlow](https://github.com/wenwanqing1217/mindflow) | 全栈 AI 工作流平台 | `wenwanqing1217/mindflow` |
| [mindflow-ds](https://github.com/wenwanqing1217/mindflow-ds) | AI 自主电商运营 | `wenwanqing1217/mindflow-ds` |
| [mindflow-variety](https://github.com/wenwanqing1217/mindflow-variety) | AI 推理综艺互动 | `wenwanqing1217/mindflow-variety` |
| [mindflow-brain](https://github.com/wenwanqing1217/mindflow-brain) | Agent 编排调度层 | `wenwanqing1217/mindflow-brain` |
| [mindflow-aid](https://github.com/wenwanqing1217/mindflow-aid) | 数字身份基础设施 | `wenwanqing1217/mindflow-aid` |

> **MindFlow = AID（身份层） × Agent 执行层（工作流）**  
> 全球唯一一个把数字身份层和 Agent 工作流打通的平台。

## 核心能力

- **DID 身份**: `did:aid:` 去中心化身份，Ed25519 密钥对
- **三层记忆**: 工作记忆 / 情景记忆 / 语义记忆
- **Ghost Layer**: 后台常驻，用户无感的数字灵魂层
- **I2I 协议**: Agent 之间身份到身份的协作
- **MCP 注入**: 把身份注入到 Claude/Cursor 等 AI 工具

## 快速开始

```bash
cd AID
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
aid init
```

## 与 MindFlow 的集成

AID 为 MindFlow 提供：
1. **DID 注入**: 工作流执行前注入执行者身份
2. **记忆查询**: Agent 可查询用户历史偏好和上下文
3. **I2I 协作**: Agent 之间通过 DID 进行身份认证的协作
4. **Proof of Execution**: 工作流执行的不可篡改记录