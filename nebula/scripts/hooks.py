"""pre-commit 钩子配置。"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def _run(cmd: list[str], **kwargs: Any) -> None:
    """运行命令，失败时退出。"""
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, **kwargs)
    if result.returncode != 0:
        sys.exit(result.returncode)


def _get_project_root() -> Path:
    """获取项目根目录。"""
    return Path(__file__).resolve().parent.parent


def format_code() -> None:
    """格式化代码。"""
    root = _get_project_root()
    _run([sys.executable, "-m", "ruff", "check", str(root), "--fix"])


def lint_code() -> None:
    """代码检查。"""
    root = _get_project_root()
    _run([sys.executable, "-m", "ruff", "check", str(root)])


def type_check() -> None:
    """类型检查。"""
    root = _get_project_root()
    _run([sys.executable, "-m", "mypy", str(root / "src")])


def run_tests() -> None:
    """运行测试。"""
    root = _get_project_root()
    _run([sys.executable, "-m", "pytest", "tests/", "-x", "-q"])


if __name__ == "__main__":
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "format":
            format_code()
        elif cmd == "lint":
            lint_code()
        elif cmd == "typecheck":
            type_check()
        elif cmd == "test":
            run_tests()
        else:
            print(f"Unknown command: {cmd}")
            sys.exit(1)
    else:
        print("Usage: python hooks.py [format|lint|typecheck|test]")
        sys.exit(1)
