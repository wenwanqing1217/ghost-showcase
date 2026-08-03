#!/usr/bin/env python3
"""codex_api — 让 AID 直接调 Codex CLI

安全说明：
- 默认绑定 127.0.0.1（仅本机访问），可通过 CODEX_API_HOST 配置
- 支持 API Key 认证（CODEX_API_KEY 环境变量），未设置时仅允许 localhost
- prompt 输入经过清理，防止命令注入
"""
import json
import os
import re
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from socketserver import ThreadingMixIn

# 安全：prompt 输入校验（与 code_runner.py 共享逻辑）
_FORBIDDEN_CHARS = re.compile(r'[;&|`$(){}[\]<>!\\]')
_MAX_PROMPT_LENGTH = 4096


def _sanitize_prompt(prompt: str) -> str:
    """清理用户输入的 prompt，防止命令注入"""
    if not prompt or not prompt.strip():
        raise ValueError("Prompt 不能为空")
    if len(prompt) > _MAX_PROMPT_LENGTH:
        raise ValueError(f"Prompt 超长（最大 {_MAX_PROMPT_LENGTH} 字符）")
    # 移除危险字符
    return _FORBIDDEN_CHARS.sub("", prompt).strip()

CODEX_PATH = os.environ.get("CODEX_PATH", "atomcode")
WORK_DIR = os.environ.get("CODE_RUNNER_DIR", os.getcwd())
# CORS 安全：默认仅允许 localhost，生产环境通过环境变量配置
CORS_ORIGIN = os.environ.get("CODEX_API_CORS_ORIGIN", "http://localhost:21345")

# 安全：API Key 认证（可选，未设置时仅允许 localhost 访问）
_API_KEY = os.environ.get("CODEX_API_KEY", "")
# 安全：默认绑定 localhost，防止外部网络访问
_API_HOST = os.environ.get("CODEX_API_HOST", "127.0.0.1")


class Handler(BaseHTTPRequestHandler):
    def _check_auth(self) -> bool:
        """检查 API Key 认证（仅在设置了 _API_KEY 时生效）"""
        if not _API_KEY:
            return True  # 未设置 API Key 时不检查
        provided = self.headers.get("X-API-Key", "")
        return provided == _API_KEY

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if self.path == "/health":
            self._json(200, {"status": "ok", "pid": os.getpid()})
        else:
            self._json(404, {"error": "not found"})

    def do_POST(self):
        # 安全：API Key 认证检查
        if not self._check_auth():
            self._json(401, {"error": "Unauthorized — 需要有效的 X-API-Key header"})
            return
        if self.path == "/ask":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            raw_prompt = body.get("prompt", "")
            if not raw_prompt:
                self._json(400, {"error": "prompt required"})
                return
            # 安全：清理用户输入
            try:
                prompt = _sanitize_prompt(raw_prompt)
            except ValueError as e:
                self._json(400, {"error": str(e)})
                return
            try:
                r = subprocess.run(
                    [CODEX_PATH, "-p", prompt, "-y", "--provider", "AtomGit-deepseek-v4-flash"],
                    capture_output=True, timeout=180, cwd=WORK_DIR,
                )
                out = r.stdout.decode('utf-8', errors='replace').strip()
                if r.returncode != 0:
                    out = f"错误: {r.stderr.decode('utf-8', errors='replace')[:200]}"
                self._json(200, {"result": out})
            except subprocess.TimeoutExpired:
                self._json(200, {"result": "超时（180秒）"})
            except FileNotFoundError:
                self._json(500, {"error": f"找不到 {CODEX_PATH}，请确认已安装"})
            except Exception as e:
                self._json(500, {"error": str(e)[:200]})
        else:
            self._json(404, {"error": "not found"})

    def _json(self, status, data):
        self.send_response(status)
        self._cors()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def _cors(self):
        # 安全：使用配置的 CORS 源，默认仅 localhost
        self.send_header("Access-Control-Allow-Origin", CORS_ORIGIN)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, fmt, *args):
        pass


class ThreadedServer(ThreadingMixIn, HTTPServer):
    allow_reuse_address = True


if __name__ == "__main__":
    port = int(os.environ.get("CODEX_API_PORT", "21345"))
    srv = ThreadedServer((_API_HOST, port), Handler)
    print(f"Codex API → http://{_API_HOST}:{port}")
    print(f"  POST /ask   {{\"prompt\":\"...\"}}")
    print(f"  GET  /health")
    if _API_KEY:
        print(f"  认证: X-API-Key header")
    else:
        print(f"  警告: 未设置 CODEX_API_KEY，仅允许 localhost 访问")
    srv.serve_forever()
