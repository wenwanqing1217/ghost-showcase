# 工作区根目录审计报告

> 审计时间：2026-07-21
> 审计范围：`D:/MW` 根目录本身（不含 mindflow-map / mindflow / DS / ai综艺 / zcode-brain / AID 六个子项目内部，由各项目单独审计）
> 执行方式：只读核查 + 非破坏性文档修复；未做任何 git 变更、未删除任何文件

---

## 一、现状概览

根目录是一个作品集元仓库（portfolio meta-repo）：

- 5 个 git submodule：`mindflow`、`DS`、`ai综艺`、`zcode-brain`、`AID/projects`（见 `.gitmodules`）
- 1 个普通子目录仓库：`mindflow-map`（有自己的 `.git`，但未注册为 submodule）
- 根级文档/脚本：`README.md`、`PORTFOLIO.md`、`DEPLOY.md`、`Caddyfile`、`build-all.bat`、`start-demo.bat`、`start_aid.bat`、`start_server.bat`、`demo/`、`docs/`、`scripts/`、`skills/`
- 大量命令事故与运行残留（见下）

`git ls-files` 核查结论：`mkdir/`、`new/-p/`、`echo/`、`Done/`、`ngrok/`、`_server.log`、`_tunnel.log`、`_startup_err.txt`、`mindflow_map.db`、`.coverage`、`1.md`、`nul` **均未被 git 跟踪**（`new/` 下另有 4 个文件例外，见失误 3）。根目录也**没有 `.env` 被 git 跟踪**。

---

## 二、决策失误清单（带证据）

### 1. 根级文档端口全面虚构【已修复】

README/PORTFOLIO/start-demo.bat/Caddyfile 全部声称 MindFlow 端口 1001/2001、DS 端口 3002，与实际代码完全不符：

- MindFlow Web 实际 3000：`mindflow/apps/web/package.json` → `"dev": "next dev -p 3000"`
- MindFlow API 实际 3001：`mindflow/apps/api/src/index.ts:40` → `Number(process.env.PORT) || 3001`；`mindflow/.env` → `PORT=3001`
- DS 实际 3000：`DS/package.json` → `"dev": "next dev"`（无 `-p`），`next.config.js` 无端口配置，`DS/.env` 无 `PORT=` 覆盖

附带问题：MindFlow Web 与 DS 默认端口同为 3000，而 `start-demo.bat` 的"全部启动"选项会把两者同时拉起，第二个启动的必然端口冲突——文档对此只字未提。

### 2. README 引用不存在的脚本【已修复】

原 `README.md:20-27` 引导 Mac/Linux 用户执行 `./build-all.sh` 和 `./start-demo.sh`，仓库中根本没有这两个文件（`ls *.sh` 为空），只有 Windows `.bat`。

### 3. 命令事故产物散落根目录

- `mkdir/`：空目录，疑似 `mkdir` 命令参数写错的产物
- `new/-p/`：空目录，典型的 cmd 下执行 `mkdir new -p` 的事故（cmd 把 `-p` 当成目录名）
- `echo/`、`Done/`：空目录，疑似重定向/占位事故
- `nul`：0 字节文件，Git Bash 下 `> nul`（Windows 写法）在 bash 里创建了真实文件

以上均未被 git 跟踪，且 `.gitignore` 已覆盖。**例外**：`new/` 下有 4 个文件仍被 git 跟踪（`new/ZCODE-ARCHITECTURE.md`、`new/codetime-machine/README.md`、`new/mindflow/README.md`、`new/mindflow/MINDFLOW-AID-FUSION.md`），`.gitignore` 的 `new/` 条目对已跟踪文件无效，需要 `git rm --cached` 才能真正移除（git 变更操作，列入提案）。

### 4. 运行时垃圾直接堆在仓库根

| 文件 | 大小 | 来源 |
|------|------|------|
| `_server.log` | 25KB | mindflow-map uvicorn 服务日志 |
| `_tunnel.log` | 247B | ngrok/servo 隧道日志 |
| `_startup_err.txt` | 864B | 启动失败 traceback dump |
| `mindflow_map.db` | 139KB | SQLite 运行时库，落在根目录是因为 `mindflow-map/src/mindflow_map/config.py:83` 默认 `sqlite+aiosqlite:///./mindflow_map.db` 用了**相对路径**，从哪个目录启动就生成在哪 |
| `.coverage` | 53KB | pytest coverage 数据 |
| `ngrok/ngrok.exe` | **32MB** | 第三方二进制 |
| `ngrok.zip` | **12MB** | 上述二进制的安装包 |

均未被 git 跟踪；`_startup_err.txt` 此前不被任何 ignore 规则覆盖（`*.log` 匹配不到 `.txt`），已在本次补入 `.gitignore`。

### 5. `1.md`：44KB 讨论纪要躺在根目录【提案】

内容是 2026-07-18 ~ 07-21 的 "aid + mindflow 全板块讨论纪要"（1160 行产品调研/设计笔记），有保留价值，但文件名无意义、位置错误，应移入 `docs/` 并重命名。

### 6. 测试数字口径混乱【部分修复】

- `PORTFOLIO.md` 原写"总计测试： 1186+ passed"，但其自身表格 32+20+10+221+923=1206，`README.md` 也写 1206+——算术错误，已改为 1206+
- `demo/portfolio.json` 声称 zcode-brain `tests: 12`，但 `npm test`（`tsx dispatcher/test.ts`）实际只有 10 个用例；12 来自 vitest 测试文件的 `it()` 计数（dispatcher 10 + safety 2），而 **vitest 根本不在 `zcode-brain/package.json` 的依赖里**，`npx vitest run` 无法直接运行。PORTFOLIO.md 原有"运行 npx vitest run 展示 12 个正式测试"的不实指引，已改为如实描述
- `demo/portfolio.json` 只覆盖 4 个项目，缺 mindflow-map 和 AID，与 README"6 个项目"口径脱节（列入提案）
- 各子项目测试数字（221/32/20/10/923）由对应项目代理实际运行验证，本次根级审计只核对了口径与算术

### 7. `demo/verify.js` 死代码【已修复】

原 53-61 行与 86-92 行是完全重复的 buildCheck 检查块（第二处永远不会打印不同结果），已删除重复块。

### 8. DEPLOY.md 引用旧路径【已修复】

- `D:\mindflow-workspace` 出现 7 处，实际工作区是 `D:\MW`，已全部替换
- 引用 `new/MINDFLOW-AID-FUSION.md`，实际文件在 `new/mindflow/MINDFLOW-AID-FUSION.md`，已修正

### 9. README.md 项目结构代码块未闭合【已修复】

文件末尾 `项目结构` 的 ``` 代码围栏在 `demo/` 行戛然而止，没有闭合标记，且结构清单缺 `codetime-machine/`、`skills/`。已补全并闭合。

### 10. `docs/screenshot_response.json`：API 响应 dump 被当文档提交【提案】

内容是浏览器自动化 API 的原始 JSON 响应（capabilities/currentUrl 等），属于调试残留，被提交进了 docs/ 目录，建议删除或归档。

### 11. `skills/baidu-ai-map/`：第三方包 vendor 进 git【提案】

是从 clawhub 注册表安装的百度地图 Agent skill（`_meta.json` 含 ownerId/version/publishedAt，`.clawhub/origin.json` 显示 registry 为 clawhub.ai），属于第三方依赖，混在自研仓库里被 git 跟踪（SKILL.md、_meta.json、skill-card.md）。需要 `BAIDU_MAP_AUTH_TOKEN` 环境变量（未发现硬编码密钥）。建议从 git 移除并改为包管理器安装。

### 12. `codetime-machine/`：只有 README 的占位项目被跟踪【提案】

自述"🚧 构思阶段"，没有任何代码，且在 `new/codetime-machine/README.md` 有一份重复副本。占位项目让"6 个项目"的作品集口径变得含糊（README 项目结构原本都不敢列它）。

### 13. 入口脚本割裂且不可移植【提案】

- `start_server.bat:11-12` 硬编码绝对路径 `D:\MW\mindflow-map`，换机器/换路径即失效，应改用 `%~dp0`
- `start-demo.bat` 菜单只有 4 个项目，mindflow-map（`start_server.bat`）和 AID（`start_aid.bat`）入口割裂
- `start_aid.bat` 与 `start_server.bat` 未被 git 跟踪（新增未提交），`Caddyfile` 同样未跟踪

### 14. `scripts/github_sync.py` 自动提交推送风险【提案】

脚本对 4 个仓库无差别 `git add .` → 自动 commit → push（`scripts/github_sync.py:92-109`），没有 dry-run、没有确认交互、没有忽略规则之外的审查，很容易把未审查的垃圾文件或密钥一并推上 GitHub。建议默认 dry-run 并加确认。

### 15. 历史审计报告结论已过时（无需动作）

`docs/ACCEPTANCE_REPORT.md:84` 声称 "DS/.env 被 git 追踪"。本次核实：DS 仓库只跟踪 `.env.example`，`.env` 未被跟踪——该问题已被修复，历史报告无需改动（它是 2026-07-19 的时点快照）。

---

## 三、已应用的修复（全部为非破坏性改动）

| 文件 | 改动 |
|------|------|
| `README.md` | 端口 1001/2001→3000/3001、3002→3000（共 3 处）；删除不存在的 build-all.sh / start-demo.sh 指引，改为如实说明仅提供 Windows 脚本；补全并闭合项目结构代码块（新增 codetime-machine/、skills/） |
| `PORTFOLIO.md` | 端口修正 4 处；总计测试 1186+→1206+；vitest 不实指引改为如实描述；技术栈表 "Vitest"→"tsx 测试脚本"；结构块标题 mindflow-workspace/→Ghost/ |
| `start-demo.bat` | 打印端口修正 4 处（菜单、:mindflow、:ds、:all） |
| `Caddyfile` | 注释端口 1001→3000、3002→3000（含生产示例块 2 处），并标注 MindFlow Web 与 DS 的 3000 端口冲突 |
| `DEPLOY.md` | `D:\mindflow-workspace`→`D:\MW`（7 处）；融合文档路径→`new/mindflow/MINDFLOW-AID-FUSION.md` |
| `demo/verify.js` | DS demoUrl 3002→3000；删除重复的 buildCheck 死代码块 |
| `demo/portfolio.json` | DS frontend→3000；zcode-brain tests 12→10；summary.totalTests 64→62 |
| `.gitignore` | 新增 `/_startup_err.txt`（验证后 `git status` 中该文件已消失） |

## 四、验证结果

- `node --check demo/verify.js` 通过；`demo/portfolio.json` JSON 解析通过（totalTests=62）
- 全库 grep 确认根级文档不再残留 `localhost:1001/2001/3002`、`build-all.sh`、`start-demo.sh`、`mindflow-workspace`（仅 `docs/ACCEPTANCE_REPORT.md` 历史快照保留旧路径，属正常）
- `git status` 确认 `_startup_err.txt` 已被忽略；确认根级无 `.env` 被跟踪
- 根目录本身没有测试/构建可跑；子项目测试由各项目代理验证

---

## 五、待确认提案（删除/高风险项，本次一律未执行）

| # | 提案 | 影响面 | 工作量 |
|---|------|--------|--------|
| 1 | 删除空目录 `mkdir/`、`new/-p/`、`echo/`、`Done/` 和 0 字节文件 `nul` | 无引用，未被跟踪，零风险 | 1 分钟 |
| 2 | 删除运行残留 `_server.log`、`_tunnel.log`、`_startup_err.txt`、`.coverage`、`mindflow_map.db` | db 运行时可再生成；注意 mindflow-map 从根目录启动会重新生成 | 1 分钟 |
| 3 | 删除 `ngrok/ngrok.exe`（32MB）+ `ngrok.zip`（12MB） | 释放 44MB；隧道工具改为用时再下载 | 1 分钟 |
| 4 | `1.md` 移入 `docs/` 并重命名（如 `docs/aid-mindflow-讨论纪要.md`） | 内容有保留价值 | 1 分钟 |
| 5 | `git rm --cached new/` 解除 4 个已跟踪文件，或整体删除 `new/`（内容为正式项目的历史快照） | 涉及 git 变更；DEPLOY.md 引用了 `new/mindflow/MINDFLOW-AID-FUSION.md`，删除前需先把该引用改到正式位置 | 10 分钟 |
| 6 | 删除或归档 `docs/screenshot_response.json` | 无引用 | 1 分钟 |
| 7 | `codetime-machine/` 移入 `docs/ideas/` 或删除 | 作品集口径更清晰 | 5 分钟 |
| 8 | `skills/baidu-ai-map/` 从 git 移除（`git rm --cached`）并加入 .gitignore，改用 clawhub 管理 | 涉及 git 变更；若 agent 环境引用该路径需同步调整 | 10 分钟 |
| 9 | `scripts/github_sync.py` 增加默认 dry-run + 确认交互 | 防止垃圾/密钥被自动推送 | 0.5 小时 |
| 10 | `start_server.bat` 硬编码 `D:\MW` 改为 `%~dp0` 相对路径 | 可移植性 | 5 分钟 |
| 11 | 合并启动入口：`start-demo.bat` 菜单补 mindflow-map、AID | 体验一致性 | 0.5 小时 |
| 12 | `demo/portfolio.json` / `demo/verify.js` 补齐 mindflow-map、AID 两个项目，或标注"仅覆盖 4 项目" | 演示口径一致 | 1 小时 |
| 13 | MindFlow Web 与 DS 默认端口均为 3000 的冲突：其一改默认端口（属子项目改动，转交对应项目） | 影响"全部启动"流程 | 各项目 10 分钟 |
| 14 | mindflow-map 默认数据库相对路径 `sqlite+aiosqlite:///./mindflow_map.db` 导致 db 落在启动目录（属 mindflow-map 项目改动，转交对应项目） | 根目录不再长 db 文件 | 10 分钟 |

## 六、未能验证 / 遗留事项

- 各子项目测试数字（221/32/20/10/923）未在根级复核，依赖各项目代理的运行结果
- `DS/.env`、`mindflow/.env` 内容未读取（密钥保护），仅核查了 `PORT=` 行与 git 跟踪状态
- `mindflow_map.db` 内容未检查（可能有演示数据，删除前请确认）
- `AID/41/` 下的 9 个中文设计文档被根仓库直接跟踪（非 submodule 内容），是否保留由用户决定
