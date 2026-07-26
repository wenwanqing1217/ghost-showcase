# Ghost / Alpha-ID 全网统一问题注册表

> 本文是全网唯一问题清单。所有审计轮次中发现的问题，均在此注册，每个有唯一 ID。
> 生成规则：`<类别>-<序号>`，例如 A-01、S-01、D-01
> 类别：A=架构、S=安全、C=代码、D=设计、T=测试、O=运维、F=功能

---

## A 架构类（14 项）

| ID | 问题 | 发现轮次 | 位置 | 优先级 |
|:--:|:-----|:---------|:------|:------:|
| A-01 | core 模块 18 个写完未接（70% 死代码） | 第 1 轮 | `src/core/` | P1 |
| A-02 | Ghost.html 4300 行单体 | 第 1 轮 | `ghost.html` | P1 |
| A-03 | 双层 Gateway 架构未落地 | 第 6 轮 | Gateway 文档 | P3 |
| A-04 | 存储层碎片化（5 种读写方式） | 第 1 轮 | 全局 | P2 |
| A-05 | 环境变量命名混乱 | 第 5 轮 | 全局 | P2 |
| A-06 | 双栈撕裂（Python + Node） | 第 2 轮 | Flow | P3 |
| A-07 | 两个独立 FastAPI 入口重复 | 第 3 轮 | `main.py` vs `web.py` | P2 |
| A-08 | entrypoints 3 个入口从未启动 | 第 3 轮 | `entrypoints/` | P2 |
| A-09 | Gateway 6 个注册路由从 Flow→alphaid 已改，但未验证端到端 | 第 4 轮 | `gateway/app.py` | P1 |
| A-10 | 未使用的 Docker 配置（4 个 compose 文件从未启动） | 第 5 轮 | `docker-compose*.yml` | P3 |
| A-11 | root core/ 目录孤立（14 TS 文件 0 引用 Ghost） | 第 5 轮 | `core/` | P3 |
| A-12 | codex-remote/ 目录空壳 | 第 5 轮 | `codex-remote/` | P3 |
| A-13 | 无数据库迁移机制 | 第 6 轮 | 全局 | P2 |
| A-14 | 775 个测试用户无清理策略 | 第 6 轮 | `alpha_id.db` | P2 |

## S 安全类（12 项）

| ID | 问题 | 发现轮次 | 位置 | 优先级 |
|:--:|:-----|:---------|:------|:------:|
| S-01 | 百度地图 Token 硬编码在源码 | 第 3 轮 | `travel.py:15` | P0 |
| S-02 | PostgreSQL 默认密码 | 第 5 轮 | `docker-compose.postgres.yml` | P0 |
| S-03 | `aid-api` 入口坏（指向已删模块） | 第 2 轮 | `pyproject.toml` | P0 |
| S-04 | `aid-daemon` 入口坏（指向已删模块） | 第 2 轮 | `pyproject.toml` | P0 |
| S-05 | `rotate_token` 无防重放（已修） | 第 3 轮 | `auth/jwt.py` | ✅ 已修 |
| S-06 | JWT 密钥模块级缓存 | 第 6 轮 | `auth/jwt.py:14` | P1 |
| S-07 | 缺少全局请求限流 | 第 6 轮 | Gateway/alphaid | P1 |
| S-08 | 前端 innerHTML XSS 风险 | 第 3 轮 | `ghost.html:4271` | P1 |
| S-09 | 飞书 WS 无心跳保活 | 第 3 轮 | `nebula/feishu.py` | P2 |
| S-10 | Ed25519 零公钥验签通过 | 第 5 轮 | `did.py:170-192` | P2 |
| S-11 | 前后端无 CSRF 保护 | 第 6 轮 | `ghost.html` | P2 |
| S-12 | `verify` 函数未检查身份元素 | 第 5 轮 | `did.py:187` | P3 |

## C 代码质量类（10 项）

| ID | 问题 | 发现轮次 | 位置 | 优先级 |
|:--:|:-----|:---------|:------|:------:|
| C-01 | `registration.py` 直连 SQLite（4 处） | 第 3 轮 | `api/registration.py` | P1 |
| C-02 | `user_identity.py` 默认 `JsonStorage`（已修） | 第 3 轮 | `user_identity.py:56` | ✅ 已修 |
| C-03 | `dual_chain.py` 默认 `JsonStorage`（已修） | 第 3 轮 | `dual_chain.py:114` | ✅ 已修 |
| C-04 | 双重编码问题：`_b64url_decode` padding 处理 | 第 5 轮 | `auth/jwt.py:71` | P3 |
| C-05 | 解密失败静默吞异常 | 第 5 轮 | `dual_chain.py:224` | P2 |
| C-06 | 用户 ID 时间戳冲突风险 | 第 5 轮 | `user_identity.py:145` | P2 |
| C-07 | ghost.html 全局变量污染 | 第 3 轮 | `ghost.html:3803` | P2 |
| C-08 | 前端硬编码置信度数据（0.94、0.92 等） | 第 3 轮 | `ghost.html:2912` | P2 |
| C-09 | 16 次提交调试文件到 git 历史 | 第 2 轮 | `final_reply.txt` 等 | P3 |
| C-10 | `__pycache__` 被提交 | 第 2 轮 | 子模块 | P3 |

## D 设计类（8 项）

| ID | 问题 | 发现轮次 | 位置 | 优先级 |
|:--:|:-----|:---------|:------|:------:|
| D-01 | 注册后无啊哈时刻 | 第 6 轮 | 注册流程 | P1 |
| D-02 | 41 文档与代码差距约 60% | 第 5 轮 | `41/` 目录 | P2 |
| D-03 | 无目标用户定义 | 第 6 轮 | 产品定位 | P1 |
| D-04 | 无多语言/国际化 | 第 6 轮 | `ghost.html` | P3 |
| D-05 | 无移动端适配 | 第 6 轮 | `ghost.html` | P3 |
| D-06 | Ghost 与 Alpha-ID 品牌关系未定义 | 第 6 轮 | 品牌定位 | P2 |
| D-07 | 无产品 Roadmap，只有技术概念 | 第 6 轮 | 产品规划 | P2 |
| D-08 | PyPI 包名与本地不一致 | 第 2 轮 | `pyproject.toml` vs PyPI | P0 |

## T 测试类（6 项）

| ID | 问题 | 发现轮次 | 位置 | 优先级 |
|:--:|:-----|:---------|:------|:------:|
| T-01 | 37 个测试需 `--noconftest` 才能收集 | 第 3 轮 | `tests/` | P1 |
| T-02 | CI 从未跑绿 | 第 2 轮 | `.github/workflows/` | P1 |
| T-03 | 3 个测试文件引用已删模块（已修） | 第 2 轮 | `tests/` | ✅ 已修 |
| T-04 | conftest.py import 已删模块（已修） | 第 2 轮 | `tests/conftest.py` | ✅ 已修 |
| T-05 | README 说 "928 tests passing" 不实 | 第 2 轮 | `README.md` | P1 |
| T-06 | taskipy 脚本全部不可用 | 第 4 轮 | `pyproject.toml` | P2 |

## O 运维类（6 项）

| ID | 问题 | 发现轮次 | 位置 | 优先级 |
|:--:|:-----|:---------|:------|:------:|
| O-01 | 无发布流程（15 版无自动化） | 第 6 轮 | PyPI | P2 |
| O-02 | 无错误监控 | 第 6 轮 | 全局 | P2 |
| O-03 | 3 服务日志各自为政 | 第 6 轮 | 全局 | P3 |
| O-04 | 无版本 tag | 第 5 轮 | git | P2 |
| O-05 | 依赖声明不全（缺 fastapi/uvicorn/httpx） | 第 4 轮 | `pyproject.toml` | P1 |
| O-06 | `requires-python = ">=3.12"` 限制过严 | 第 4 轮 | `pyproject.toml` | P2 |

## F 功能缺失类（6 项）

| ID | 问题 | 发现轮次 | 位置 | 优先级 |
|:--:|:-----|:---------|:------|:------:|
| F-01 | 无邮箱注册/密码重置 | 第 6 轮 | API 层 | P2 |
| F-02 | CLI 与 Web 不共享用户状态 | 第 6 轮 | CLI vs API | P2 |
| F-03 | 无数据删除/导出功能 | 第 6 轮 | API 层 | P2 |
| F-04 | 无隐私政策/用户协议 | 第 6 轮 | 根目录 | P2 |
| F-05 | 无 CONTRIBUTING.md | 第 6 轮 | 根目录 | P3 |
| F-06 | Ghost.html 9 面板仅 2 个有真实数据 | 第 1 轮 | `ghost.html` | P1 |

---

## 统计

| 类别 | 数量 | 已修 | 待修 |
|:-----|:----:|:----:|:----:|
| A 架构 | 14 | 0 | 14 |
| S 安全 | 12 | 1 | 11 |
| C 代码质量 | 10 | 2 | 8 |
| D 设计 | 8 | 0 | 8 |
| T 测试 | 6 | 2 | 4 |
| O 运维 | 6 | 0 | 6 |
| F 功能缺失 | 6 | 0 | 6 |
| **总计** | **62** | **5** | **57** |

**62 项问题，5 项已修复，57 项待修复。**
