# MindFlow 多仓库审计验收报告

> 审计时间: 2026-07-19
> 审计范围: mindflow-map / AID / DS / mindflow
> 执行人: ZCode 自动化审计 + 多智能体并行探索

---

## 一、mindflow-map（主仓库）

### 状态: 已修复，可交付

**P0 - 关键安全 (4项) ✅ 已修复**
| 问题 | 文件 | 修复内容 |
|------|------|----------|
| 微信签名绕过 | `src/mindflow_map/api/wechat.py` | `_check_signature` 在 `WECHAT_TOKEN` 缺失时从静默跳过改为抛出 `HTTPException(500)` |
| URL 注入 | `src/mindflow_map/api/wechat.py` | Access Token URL 参数由 f-string 改为 `params=dict` |
| 类型缺失 NameError | `src/mindflow_map/config_validator.py` | 补全 `__future__ annotations` 与 `typing` 导入 |
| 配置属性名错误 | `src/mindflow_map/identity/aid_client.py` | 修正环境变量名以匹配 config |

**P1 - 严重 bug/不稳定 (6项) ✅ 已修复**
| 问题 | 文件 | 修复内容 |
|------|------|----------|
| 线程不安全 | `src/mindflow_map/workflows/engine.py` | 移除 `asyncio.set_event_loop()` 调用 |
| 嵌套 executor 反模式 | `src/mindflow_map/workflows/engine.py` | 重写 `execute_parallel` 为纯 `asyncio.gather` |
| 私有属性访问 | `src/mindflow_map/workflows/engine.py` | `_executor._max_workers` → 实例变量 |
| SSRF 风险 | `src/mindflow_map/automation/shopify.py` | 增加 `shop_domain` 正则校验 |
| JSON 解析异常 | `src/mindflow_map/automation/douyin.py` | 增加 `json.JSONDecodeError` 处理 |
| 单例生命周期 | `src/mindflow_map/main.py` | `WorkflowEngine` 迁移到 lifespan 上下文 |

**测试结果**: 43/43 passed ✅
**提交**: `cabe6a5` - fix(P0/P1): 安全与稳定性审计修复

---

## 二、AID 仓库（Alpha-ID 数字身份系统）

### P0 - 关键安全 (4项) ⚠️ 需修复

| # | 问题 | 位置 | 风险 | 建议修复 |
|---|------|------|------|----------|
| 1 | **暴露真实 API 密钥** | `projects/.env:3` | `OPENAI_API_KEY` 明文写在 `.env` 中 | 确认 `.env` 未推送远端；轮换该密钥；使用密钥管理服务 |
| 2 | **JWT 硬编码默认密钥** | `src/auth/jwt.py:17-21` | 未配置 `AUTH_MASTER_KEY` 时使用公开默认值，可伪造任意用户令牌 | 启动时校验密钥长度，缺失则拒绝启动 |
| 3 | **设备指纹校验绕过** | `src/api/identity.py:47-50` | `if ... not in devices: pass` 允许任意设备登录 | 移除 `pass`，应返回 403 或要求先绑定设备 |
| 4 | **SSRF 通过未校验的 OPENAI_BASE_URL** | `src/core/agent.py:467-468`, `src/alpha_id/web.py:322-323` | 环境变量直接用作 LLM 请求目标，可被重定向到内网服务 | 增加 URL schema + host 白名单校验 |

### P1 - 严重 bug/不稳定 (6项) ⚠️ 需修复

| # | 问题 | 位置 | 风险 | 建议修复 |
|---|------|------|------|----------|
| 5 | **CORS 通配符 + 凭证** | `src/main.py:26-33` | 任意源可携带凭证访问 API | 限制为具体域名 |
| 6 | **exec() 执行技能代码** | `src/alpha_id/skill_signer.py:504-512` | 从磁盘加载并执行任意 Python 代码，无沙箱 | 增加沙箱限制或使用更安全的插件机制 |
| 7 | **os.system() 命令注入** | `src/codex.py:106-107` | 使用 shell 执行脚本，路径注入风险 | 改用 `subprocess.run([...])` 参数化调用 |
| 8 | **SQL 注入风险** | `src/alpha_id/collectors/cursor.py:82` | 表名通过 f-string 直接拼入 SQL | 对表名进行白名单校验 |
| 9 | **E2E 测试导入失败** | `tests/integration/test_e2e_api.py:19` | `main.py` 相对导入与顶层导入冲突 | 统一包结构，修复导入路径 |
| 10 | **异常吞没** | `daemon.py`, `fairy_agent.py` 等多处 | `except Exception: pass` 静默丢弃错误 | 至少记录日志，关键路径抛出异常 |

### P2 - 设计问题 (4项)

| # | 问题 | 位置 | 建议 |
|---|------|------|------|
| 11 | 统计接口公开 | `src/api/identity.py:109-112` | 增加认证或移除 |
| 12 | 守护线程资源泄漏 | `daemon.py` 等多处 | 使用 `threading.Thread(daemon=False)` + 优雅关闭 |
| 13 | 自动注册导致用户枚举 | `src/alpha_id/web.py:224-244` | 登录前强制设备绑定 |
| 14 | `.env.example` 硬编码默认密码 | `projects/.env.example:8-9` | 使用 `change-me` 占位符 |

### 测试状态
- 866 个测试通过（排除 E2E 测试集合错误）
- E2E 测试因导入问题无法收集

### 凭证安全
- ⚠️ `projects/.env` 包含真实 API 密钥（已确认未被 git 追踪）
- `projects/codex-bridge/.env` 包含 DeepSeek API 密钥（已确认未被 git 追踪）
- **建议**: 立即轮换 `OPENAI_API_KEY` 和 `DEEPSEEK_API_KEY`

---

## 三、DS 仓库（DeepSeek 电商仪表盘）

### P0 - 关键安全 (2项) ⚠️ 需修复

| # | 问题 | 位置 | 风险 | 建议修复 |
|---|------|------|------|----------|
| 1 | **`.env` 被 git 追踪** | `D:\mindflow-workspace\DS\.env` | 环境变量提交到版本控制，历史中永久留存 | `git rm --cached .env` + 清理历史（`bfg` 或 `git filter-repo`） |
| 2 | **全部 API 路由无认证** | `src/app/api/**/route.ts` | 任何未授权用户可创建订单、触发付费 OpenAI 调用 | 增加 `middleware.ts` + NextAuth 或 API Key 校验 |

### P1 - 严重 bug/不稳定 (5项) ⚠️ 需修复

| # | 问题 | 位置 | 风险 | 建议修复 |
|---|------|------|------|----------|
| 3 | **Shopify SSRF** | `src/lib/shopify/client.ts:24-28` | `shopifyUrl()` 拼接未校验域名，可构造任意 HTTPS 请求 | 增加 `^[a-z0-9-]+\.myshopify\.com$` 正则校验 |
| 4 | **健康检查产生副作用** | `src/app/api/health/route.ts:39-44` | 每次健康检查调用 OpenAI + Shopify 真实 API，产生费用和限流 | 改为检查配置可达性，或增加缓存 TTL |
| 5 | **POST 端点无输入校验** | `src/app/api/agents/content/approve/route.ts:17-27` | 直接解构 `request.json()` 无 schema 验证 | 增加 Zod schema 校验 |
| 6 | **JSON.parse 无 try/catch** | `src/app/api/agents/cs/tickets/route.ts:25` | 解析 `metadata` 字段时异常崩溃 | 增加 try/catch |
| 7 | **内存限流器在 Serverless 失效** | `src/lib/middleware/rate-limit.ts` | 进程内 Map 存储，Vercel 每次请求可能命中不同实例 | 使用 Redis/Upstash 存储 |

### P2 - 设计问题 (5项)

| # | 问题 | 位置 | 建议 |
|---|------|------|------|
| 8 | 错误响应返回 `success: true` | `alerts/route.ts`, `cs/tickets/route.ts` 等 | 统一错误响应格式为 `success: false` |
| 9 | 8 个测试失败 | `alerts/page.test.tsx`, `ads/page.test.tsx` 等 | 更新或删除失效测试 |
| 10 | 提示词注入 | `src/lib/agents/content-agent.ts:8-14` | 对用户输入进行转义或隔离 |
| 11 | 缺少安全头 | `next.config.js` | 增加 CSP, X-Frame-Options 等 |
| 12 | 无 CORS 配置 | `vercel.json`, `next.config.js` | 增加 CORS 中间件或 Vercel 安全头 |

### 测试状态
- 8/16 tests failing
- 失败原因: UI 测试与组件实现不同步（查找不存在的文本如 "Mark all read"）

### 凭证安全
- ⚠️ `.env` 已被 git 追踪，但当前值为占位符（`shpat_xxx`, `sk-xxx`）
- `.gitignore` 已包含 `.env`，但文件已存在于历史中
- **建议**: 清理 git 历史中的 `.env`

---

## 四、mindflow 仓库（MindFlow 平台）

### P0 - 关键安全 (3项) 🚨 需立即修复

| # | 问题 | 位置 | 风险 | 建议修复 |
|---|------|------|------|----------|
| 1 | **未认证的 Computer Use API → RCE** | `apps/api/src/routes/computer-use.ts`, `computer-use.service.ts` | 零认证，可执行任意 JS、导航任意 URL、控制键盘鼠标 | 增加强认证 + IP 白名单，或禁用该端点 |
| 2 | **CORS 通配符 + 危险端点** | `apps/api/src/index.ts:21-23` | `origin: true` 允许所有源，配合未认证端点可跨域攻击 | 限制为具体域名 |
| 3 | **限流器密钥删除 bug → 限流绕过** | `apps/api/src/middleware/rate-limit.ts:30-31` | 清理循环删除错误的 key，导致限流失效 | 修复为删除迭代的 entry key |

### P1 - 严重 bug/不稳定 (5项) ⚠️ 需修复

| # | 问题 | 位置 | 风险 | 建议修复 |
|---|------|------|------|----------|
| 4 | **测试失败** | `apps/api/src/services/workflow.engine.test.ts:46` | `expect(result).toHaveProperty('length')` 假设返回数组，实际返回对象 | 更新测试断言或修复实现 |
| 5 | **内部错误详情泄露** | `apps/api/src/routes/aid.ts`, `map.ts`, `workflow.ts` 等多处 | 返回 `error.message` 给客户端，暴露内部实现 | 返回通用错误消息，详情只记录日志 |
| 6 | **硬编码 Windows 浏览器路径** | `apps/api/src/services/computer-use.service.ts:55` | `C:\Program Files (x86)\Microsoft\Edge\...` 在 Linux 容器中崩溃 | 改为环境变量配置 |
| 7 | **内存泄漏（限流器）** | `apps/api/src/middleware/rate-limit.ts` | 由于错误删除 key，过期条目永不清理 | 同 P0 #3 修复 |
| 8 | **CI 忽略测试失败** | `.github/workflows/ci.yml:34` | `npm test || echo "..."` 使测试失败不阻断部署 | 移除 `|| echo` |

### P2 - 设计问题 (7项)

| # | 问题 | 位置 | 建议 |
|---|------|------|------|
| 9 | Next.js 忽略构建错误 | `apps/web/next.config.js:6-10` | 移除 `ignoreBuildErrors: true` |
| 10 | XSS 风险（地图弹窗） | `apps/web/app/map/page.tsx:112` | 对外部 HTML 进行转义或使用 `DOMPurify` |
| 11 | 无请求体大小限制 | `apps/api/src/index.ts` | 增加 `bodyLimit` 配置 |
| 12 | 无认证框架 | 所有路由 | 增加 API Key 或 Session 认证 |
| 13 | fetch 无超时 | `aid.service.ts:106,157` | 增加 `AbortSignal.timeout()` |
| 14 | HTTP（非 HTTPS）外部调用 | `aid.service.ts:106` | 改为 `https://ip-api.com` |
| 15 | 客户端 `Function()` 求值器 | `apps/web/app/assistant/page.tsx:233` | 使用更安全的表达式解析器 |

### 测试状态
- `apps/api`: 15 passed, 1 failed
- `apps/web`: 通过
- `packages/shared`: 通过

### 凭证安全
- ✅ `.env` 仅包含 `PORT` 和 `NEXT_PUBLIC_API_URL`
- ✅ `.gitignore` 已包含 `.env`
- 无暴露凭证风险

---

## 五、跨仓库一致性问题

| 问题 | 影响仓库 | 严重程度 | 说明 |
|------|----------|----------|------|
| CORS 通配符 + 凭证 | mindflow-map ✅, AID ⚠️, mindflow 🚨 | P1 | 三个仓库均存在相同反模式 |
| 限流器内存泄漏 / 密钥删除 bug | DS ⚠️, mindflow 🚨 | P1-P0 | 两仓库复制了相同 bug，mindflow 中更为严重 |
| `.env` 提交问题 | AID ⚠️, DS 🚨 | P0 | AID 未追踪但包含真实密钥；DS 已追踪但值为占位符 |
| 未认证 API | DS ⚠️, mindflow 🚨 | P0-P1 | 全仓库 API 端点无统一认证 |

---

## 六、后续建议

### 立即行动（P0）- 今天完成
1. **mindflow**: 禁用或强认证保护 `/api/computer-use/*` 端点
2. **mindflow**: 修复限流器密钥删除 bug
3. **AID**: 轮换 `OPENAI_API_KEY` 和 `DEEPSEEK_API_KEY`
4. **AID**: 修复 JWT 默认密钥和认证绕过
5. **DS**: 从 git 移除 `.env` 并清理历史

### 短期修复（P1）- 本周完成
1. **全部**: 统一 CORS 配置为白名单模式
2. **AID**: 修复 SSRF、CORS、exec() 沙箱、SQL 注入
3. **DS**: 修复 Shopify SSRF、健康检查副作用、输入校验
4. **mindflow**: 修复错误泄露、Windows 路径、CI 配置

### 中期优化（P2）- 迭代中完成
1. **全部**: 建立共享的 `@mindflow/security` 包
2. **DS + mindflow**: 修复限流器内存泄漏
3. **全部**: 增加安全头（CSP, X-Frame-Options）
4. **全部**: 修复失败的测试用例

### 长期架构
1. 建立跨仓库 CI 流水线，统一 lint + test + 安全扫描
2. 增加 pre-commit hook 扫描硬编码密钥
3. 统一认证中间件（FastAPI + Fastify + Next.js）

---

## 七、审计总结

| 仓库 | P0 | P1 | P2 | 测试状态 | 凭证安全 |
|------|----|----|----|----------|----------|
| mindflow-map | 4 ✅ 已修复 | 6 ✅ 已修复 | 0 | 43/43 passed | 安全 |
| AID | 4 ⚠️ 需修复 | 6 ⚠️ 需修复 | 4 待处理 | 866 passed, 1 集合失败 | ⚠️ 真实密钥在 .env |
| DS | 2 ⚠️ 需修复 | 5 ⚠️ 需修复 | 5 待处理 | 8/16 failed | ⚠️ .env 被 git 追踪 |
| mindflow | 3 🚨 需立即修复 | 5 ⚠️ 需修复 | 7 待处理 | 15/16 passed | 安全 |

**总体评估**:
- **mindflow-map**: 已达到生产就绪状态，所有 P0/P1 已修复并提交
- **AID**: 存在严重安全问题（JWT 伪造、SSRF、代码执行），需立即处理
- **DS**: 存在严重安全问题（SSRF、未认证 API、git 追踪 .env），需立即处理
- **mindflow**: 存在 RCE 风险端点（computer-use API）和限流绕过，**需立即禁用或保护该端点**
