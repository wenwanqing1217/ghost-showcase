#!/usr/bin/env python3
"""code_runner — AID 编程技能模块
==================================
AID 总助的编程技能，背后调本地 CLI（默认 AtomCode 免费额度）。

CLI 用法:
    python code_runner.py "帮我写一个 Python 爬虫"

模块用法:
    from code_runner import BackendRunner, BACKENDS
    runner = BackendRunner()
    result = await runner.run("写个函数", chat_id="optional")
    print(result)

支持 /backend list、/status 等命令（与飞书 bot 共享同一套配置）。
"""

import asyncio
import json
import os
import re
import sys
import logging

# ============================================================
# 安全：prompt 输入校验
# ============================================================
# 禁止的字符：可能改变 CLI 行为的特殊字符
_FORBIDDEN_CHARS = re.compile(r'[;&|`$(){}[\]<>!\\]')
_MAX_PROMPT_LENGTH = 4096


def _sanitize_prompt(prompt: str) -> str:
    """清理用户输入的 prompt，防止命令注入
    
    Args:
        prompt: 用户输入的原始 prompt
        
    Returns:
        清理后的 prompt
        
    Raises:
        ValueError: 如果 prompt 包含禁止字符或超长
    """
    if not prompt or not prompt.strip():
        raise ValueError("Prompt 不能为空")
    
    if len(prompt) > _MAX_PROMPT_LENGTH:
        raise ValueError(f"Prompt 超长（最大 {_MAX_PROMPT_LENGTH} 字符）")
    
    # 检查禁止字符（防止 CLI 参数注入）
    if _FORBIDDEN_CHARS.search(prompt):
        # 只移除危险字符，而不是拒绝——更友好的用户体验
        prompt = _FORBIDDEN_CHARS.sub("", prompt)
    
    return prompt.strip()

# ============================================================
# 日志 — 输出到 stderr，不干扰 stdout 的结果输出
# ============================================================
logger = logging.getLogger("code-runner")
if not logger.handlers:
    h = logging.StreamHandler(sys.stderr)
    h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)

# ============================================================
# 多后端配置（code_runner 是单一起源，bot.py 从此导入）
# ============================================================
BACKENDS = {
    "atomcode": {
        "cmd": "atomcode",
        "args": ["-p", "{prompt}", "-y", "--provider", "AtomGit-deepseek-v4-flash"],
        "desc": "AtomCode CLI（AtomGit 免费额度）",
    },
    "zcode": {
        "cmd": "node",
        "args": ["D:\\Software\\ZCode\\resources\\glm\\zcode.cjs", "--prompt", "{prompt}", "--mode", "yolo", "--json"],
        "desc": "ZCode CLI（GLM / LongCat）",
    },
    "codex": {
        "cmd": "codex",
        "args": ["-p", "{prompt}"],
        "desc": "Codex CLI（桌面版，仅限本机）",
    },
}

# 环境变量覆盖
_custom = os.environ.get("CUSTOM_BACKEND", "").strip()
if _custom:
    parts = _custom.split(":", 2)
    if len(parts) == 3:
        BACKENDS[parts[0]] = {
            "cmd": parts[1],
            "args": parts[2].split("|"),
            "desc": f"自定义({parts[0]})",
        }

DEFAULT_BACKEND = os.environ.get("DEFAULT_BACKEND", "atomcode")
WORK_DIR = os.environ.get("CODE_RUNNER_DIR", "")  # 项目工作目录
MAX_CONCURRENT = int(os.environ.get("CODEX_MAX_CONCURRENT", "3"))
_chat_backends = {}


# ============================================================
# 核心：后端运行器
# ============================================================
class BackendRunner:
    """编程技能执行器，支持多个后端引擎"""

    def __init__(self):
        self._sem = asyncio.Semaphore(MAX_CONCURRENT)

    # ---- 后端选择 ----

    def get_backend(self, chat_id: str = "") -> str:
        return _chat_backends.get(chat_id, DEFAULT_BACKEND)

    def set_backend(self, chat_id: str, name: str) -> bool:
        if name in BACKENDS:
            _chat_backends[chat_id] = name
            return True
        return False

    def list_backends(self, current: str = "") -> str:
        lines = ["可用后端："]
        cur = self.get_backend()
        for name, cfg in BACKENDS.items():
            mark = " [当前]" if name == (current or cur) else ""
            lines.append(f"  {name} — {cfg['desc']}{mark}")
        return "\n".join(lines)

    # ---- 执行 ----

    async def run(self, prompt: str, timeout: int = 120, chat_id: str = "") -> str:
        """执行编程任务

        参数:
            prompt: 用户需求文本
            timeout: 超时秒数（默认 120）
            chat_id: 会话标识（用于记忆后端选择，可选）

        返回:
            执行结果文本
        """
        # 安全：清理用户输入
        try:
            prompt = _sanitize_prompt(prompt)
        except ValueError as e:
            return f"❌ 输入校验失败: {e}"

        async with self._sem:
            backend_name = self.get_backend(chat_id)
            backend = BACKENDS.get(backend_name)
            if not backend:
                return f"❌ 后端 '{backend_name}' 不存在，可用: {', '.join(BACKENDS.keys())}"

            cmd = backend["cmd"]
            args = [a.replace("{prompt}", prompt) for a in backend["args"]]

            logger.info("执行: %s %s", cmd, " ".join(a.replace(prompt, "...") for a in args))

            cwd = os.environ.get("CODE_RUNNER_DIR", "") or None
            logger.info("工作目录: %s", cwd or os.getcwd())
            proc = await asyncio.create_subprocess_exec(
                cmd, *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=cwd,
            )
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            except asyncio.TimeoutError:
                proc.kill()
                return f"⏰ 超时：{timeout} 秒未完成，请简化需求重试"

            if proc.returncode != 0:
                err = stderr.decode("utf-8", errors="replace")[:500]
                logger.warning("%s 返回非零: %s", backend_name, err)
                return f"❌ 执行出错 ({backend_name}):\n{err}"

            result = stdout.decode("utf-8", errors="replace").strip()
            return result or "执行完毕（无输出）"


# ============================================================
# 命令行入口
# ============================================================
async def main():
    if len(sys.argv) < 2:
        print(
            f"用法: python {os.path.basename(__file__)} \"你的编程需求\"\n"
            f"      python {os.path.basename(__file__)} /backend list\n"
            f"      python {os.path.basename(__file__)} /status\n\n"
            f"默认后端: {DEFAULT_BACKEND}（{BACKENDS[DEFAULT_BACKEND]['desc']}）",
            file=sys.stderr,
        )
        return

    text = " ".join(sys.argv[1:]).strip()
    runner = BackendRunner()

    # 处理命令
    if text.startswith("/"):
        parts = text.split()
        cmd = parts[0].lower()

        if cmd == "/backend":
            if len(parts) == 1 or parts[1] == "list":
                print(runner.list_backends())
            elif parts[1] in BACKENDS:
                runner.set_backend("cli", parts[1])
                print(f"已切换后端: {parts[1]} — {BACKENDS[parts[1]]['desc']}")
            else:
                print(f"未知后端: {parts[1]}，可用: {', '.join(BACKENDS.keys())}")
        elif cmd == "/status":
            cur = runner.get_backend("cli")
            print(f"当前后端: {cur} — {BACKENDS[cur]['desc']}")
        else:
            print(f"未知命令: {cmd}")
        return

    # 执行编程任务
    result = await runner.run(text, chat_id="cli")
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
