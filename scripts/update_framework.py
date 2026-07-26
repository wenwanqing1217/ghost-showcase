import pathlib

appendix = r'''


## 七、逐文件功能明细

### 7.1 alphaid/alpha_id/ （核心库）

| 文件 | 行数 | 功能 | 状态 |
|:-----|:----:|:-----|:----:|
| web.py | 617 | FastAPI demo app, /identity, /brain, /chat, /network | 核心完成 |
| scaffold_templates.py | 530 | 项目脚手架模板生成 | CLI工具不应在核心库 |
| agent_network.py | 442 | Agent网络: Peer管理、调用链追踪 | 有代码无真实A2A |
| skill_signer.py | 529 | Skill签名、包管理、归因追踪 | 完成 |
| skill_cli.py | 390 | Skill CLI管理 | CLI混在核心目录 |
| skill_repository.py | 334 | Skill仓库管理 | 有基础 |
| profile_schema.py | 384 | 用户画像数据模型 | 完成 |
| did.py | 321 | DID文档、注册表 | 基础实现 |
| poe.py | 324 | Proof of Execution 存证 | 完成 |
| brain_cli.py | 312 | 大脑 CLI | CLI不应在此目录 |
| profile_cli.py | 802 | 画像 CLI（最大文件） | CLI不应在此目录 |
| identity_cli.py | 676 | 身份 CLI | CLI不应在此目录 |
| signer.py | 250 | Ed25519签名 | 完成 |
| agent.py | 216 | Agent执行循环 | 完成 |
| agent_cli.py | 97 | Agent扫描/握手CLI | CLI不应在此目录 |
| detect.py | 207 | 环境检测 | 有基础 |
| social_cli.py | 181 | 社交 CLI | CLI不应在此目录 |
| scene_detection.py | 160 | 场景识别 | 半成品 |
| repo_cli.py | 150 | 仓库 CLI | CLI不应在此目录 |
| container.py | 139 | 依赖注入容器 | 核心 |
| scaffold_cli.py | 121 | 脚手架 CLI | CLI不应在此目录 |
| profile_wizard.py | 115 | 画像向导 CLI | CLI不应在此目录 |
| did_resolver.py | 107 | DID解析器 | 空壳 |
| config.py | 67 | 配置 | 完成 |
| cli.py | 55 | CLI主入口 | 完成 |
| suggest_cli.py | 85 | 建议 CLI | CLI不应在此目录 |

### 7.2 alphaid/api/ （REST 路由）

| 文件 | 行数 | 路由 | 状态 |
|:-----|:----:|:-----|:----:|
| identity.py | 158 | 11路由: register/login/refresh/logout/verify/me/user/devices/sync/session/stats | 核心 |
| models.py | 194 | Pydantic模型 | 完成 |
| dual_chain.py | 114 | 7路由: save/get/query/migrate/stats/list/delete | 完成 |
| social.py | 72 | 6路由: 好友请求/好友/消息 | 完成 |
| risk.py | 101 | 2路由: evaluate/voice-verify | 半成品 |
| shortdrama.py | 95 | 6路由: 短剧扫描/查询/审核 | 与核心无关 |

### 7.3 alphaid/auth/ （认证）

| 文件 | 行数 | 功能 | 状态 |
|:-----|:----:|:-----|:----:|
| jwt.py | 226 | JWT签发/验证/轮换/撤销 | 完整 |
| token_store.py | 103 | Token持久化存储 | 完整 |
| middleware.py | 36 | FastAPI依赖注入 | 完整 |

### 7.4 alphaid/entrypoints/ （入口）

| 文件 | 行数 | 功能 | 状态 |
|:-----|:----:|:-----|:----:|
| daemon.py | 1368 | 桌面精灵（透明球UI+Chat+MCP+OCR） | 与Web项目定位不符 |
| aid_mcp_server.py | 919 | MCP服务器: 屏幕控制/OCR/代码/记忆图 | 与daemon重复 |
| shortdrama_service.py | 287 | 短剧后台服务 | 与核心无关 |
| api.py | 79 | FastAPI Web入口 | 主入口 |

### 7.5 alphaid/tools/ （工具）

| 文件 | 行数 | 功能 | 状态 |
|:-----|:----:|:-----|:----:|
| shortdrama_tool.py | 638 | 短剧工具 | 与核心无关 |
| identity_tool.py | 331 | 身份工具 | 有用 |
| ocr.py | 327 | OCR识别 | 有用 |
| security_tool.py | 310 | 安全检查 | 有用 |
| window_control.py | 286 | 窗口控制 | 桌面端功能 |
| screen_capture.py | 195 | 截屏 | 桌面端功能 |
| tool_decorator.py | 28 | 工具装饰器 | 核心 |

### 7.6 alphaid/mindflow/ （MindFlow）

| 文件 | 行数 | 功能 | 状态 |
|:-----|:----:|:-----|:----:|
| travel.py | 396 | 出行规划 | 完成 |
| interview.py | 358 | 面试准备 | 单一场景 |
| voice_control.py | 283 | 语音控制 | 半成品 |
| engine.py | 291 | MindFlow引擎 | 完成 |
| route_optimizer.py | 294 | 路线优化 | 完成 |
| onboarding.py | 286 | 新用户引导 | 半成品 |
| user_profile.py | 192 | 用户画像 | 半成品 |
| schedule_parser.py | 137 | 日程解析 | 完成 |
| intent.py | 87 | 意图识别 | 半成品 |

---

## 八、飞书机器人完整能力评估

### 消息处理流程

飞书消息 => bot.py _on_message() => 去重 => 图片下载 => feishu.py _process_message() => workflow_engine.execute(text) => send_text()

### 能处理的指令（3个硬编码模板）

| 模板 | 触发词 | 能力 |
|:-----|:-------|:-----|
| map-navigation | "怎么去中关村" "查咖啡厅" | 地点搜索+路线规划 |
| douyin-publish | "帮我发个短剧" | AI剧本+抖音发布 |
| shopify-optimize | "优化我的店铺" | Shopify运营建议 |

### 不能做的

通用聊天、查身份/记忆、多轮对话、LLM意图识别、兜底回复

### 目标架构

飞书消息 => Gateway /v1/intent/parse (LLM) => 身份/记忆/工作流/聊天分流

---

## 九、文件结构整改建议

### 要做

1. alpha_id/ 拆成 identity/ agent/ cli/ profile/ web/
2. 删 alpha_id_zix.egg-info（和alpha_id.egg-info重复）
3. 删 entrypoints/daemon.py（桌面端，无关）
4. 删 entrypoints/shortdrama_service.py（短剧，无关）
5. 删 api/shortdrama.py + tools/shortdrama_tool.py（无关）
6. 统一双链记忆：删 flow/api 的 TS 版
7. 统一工作流引擎：删 flow/api 的 workflow.engine.ts

### 不做

- nebula 结构合理，不动
- gateway 极简，不动
- 不改成 kebab-case 命名

---

## 十、变更记录

| 日期 | 版本 | 变更 |
|:-----|:----|:------|
| 2026-07-25 | 0.3.0 | 初版: 六层架构 + 逐文件盘点 + 命名建议 |
'''

content = pathlib.Path('D:/MW/FRAMEWORK.md').read_text(encoding='utf-8')
# 如果已经有七、逐文件功能明细则跳过
if '## 七、逐文件功能明细' not in content:
    content += appendix
    pathlib.Path('D:/MW/FRAMEWORK.md').write_text(content, encoding='utf-8')
    print('OK: 已追加逐文件明细, 共 {} 行'.format(len(content.splitlines())))
else:
    print('SKIP: 已存在')
