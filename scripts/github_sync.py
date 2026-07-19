"""GitHub 多仓库同步脚本

用法：
    python scripts/github_sync.py

功能：
    1. 检查网络连通性（支持代理环境）
    2. 遍历 AID / DS / mindflow / mindflow-map 四个仓库
    3. 自动 add / commit / push 有改动的仓库
    4. 汇总输出同步结果
"""

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# 仓库列表（相对于 workspace 根目录）
REPOS = [
    ("AID", "wenwanqing1217/mindflow-aid"),
    ("DS", "wenwanqing1217/mindflow-ds"),
    ("mindflow", "wenwanqing1217/mindflow"),
    ("mindflow-map", "wenwanqing1217/mindflow-map"),
]

WORKSPACE = Path(__file__).resolve().parent.parent


def run(cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    """运行命令，返回 (returncode, stdout, stderr)"""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        shell=False,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def check_network() -> bool:
    """检查 GitHub 网络连通性，支持代理环境"""
    # 方法1: git ls-remote（最准确）
    code, _, _ = run(["git", "ls-remote", "https://github.com", "HEAD"], WORKSPACE)
    if code == 0:
        return True

    # 方法2: curl 探测（备选）
    code, _, _ = run(
        ["curl", "-sSf", "--max-time", "5", "https://github.com"],
        WORKSPACE,
    )
    return code == 0


def sync_repo(name: str, remote: str, max_retries: int = 2) -> dict:
    """同步单个仓库，支持重试"""
    repo_path = WORKSPACE / name
    result = {
        "name": name,
        "remote": remote,
        "status": "unknown",
        "message": "",
        "commits": 0,
    }

    if not repo_path.exists():
        result["status"] = "skip"
        result["message"] = "目录不存在"
        return result

    # 检查是否有改动
    code, stdout, stderr = run(["git", "status", "-s"], repo_path)
    if code != 0:
        result["status"] = "error"
        result["message"] = f"git status 失败: {stderr}"
        return result

    if not stdout:
        result["status"] = "clean"
        result["message"] = "工作区干净，无需同步"
        return result

    # 重试机制
    last_error = ""
    for attempt in range(max_retries):
        if attempt > 0:
            time.sleep(2 ** attempt)  # 指数退避

        # 暂存所有改动
        code, _, stderr = run(["git", "add", "."], repo_path)
        if code != 0:
            last_error = f"git add 失败: {stderr}"
            continue

        # 提交
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        commit_msg = f"chore: auto sync {timestamp}"
        code, _, stderr = run(["git", "commit", "-m", commit_msg], repo_path)
        if code != 0:
            last_error = f"git commit 失败: {stderr}"
            continue

        # 推送
        code, stdout, stderr = run(["git", "push"], repo_path)
        if code != 0:
            last_error = f"git push 失败: {stderr}"
            continue

        # 成功
        code, stdout, _ = run(["git", "log", "-1", "--oneline"], repo_path)
        result["status"] = "pushed"
        result["message"] = stdout or "已推送"
        result["commits"] = 1
        return result

    # 所有重试都失败
    result["status"] = "error"
    result["message"] = f"{last_error} (已重试 {max_retries} 次)"
    return result


def main():
    print("=" * 60)
    print("  MindFlow GitHub 多仓库同步")
    print("=" * 60)
    print()

    # 检查网络
    print("[*] 检查 GitHub 网络连通性...")
    if not check_network():
        print("[!] 网络不通，跳过本次同步")
        sys.exit(0)
    print("[OK] 网络正常")
    print()

    # 同步各仓库
    results = []
    for name, remote in REPOS:
        print(f"[*] 同步 {name} ({remote}) ...")
        result = sync_repo(name, remote)
        results.append(result)

        if result["status"] == "pushed":
            print(f"    -> 已推送: {result['message']}")
        elif result["status"] == "clean":
            print(f"    -> 干净，无需同步")
        elif result["status"] == "skip":
            print(f"    -> 跳过: {result['message']}")
        else:
            print(f"    -> 失败: {result['message']}")

    # 汇总
    print()
    print("=" * 60)
    print("  同步汇总")
    print("=" * 60)
    pushed = sum(1 for r in results if r["status"] == "pushed")
    clean = sum(1 for r in results if r["status"] == "clean")
    failed = sum(1 for r in results if r["status"] == "error")
    skipped = sum(1 for r in results if r["status"] == "skip")

    for r in results:
        status_icon = {
            "pushed": "[OK]",
            "clean": "[-] ",
            "error": "[ERR]",
            "skip": "[SKIP]",
        }.get(r["status"], "[?] ")
        print(f"  {status_icon} {r['name']}: {r['message']}")

    print()
    print(f"  总计: {pushed} 已推送, {clean} 干净, {failed} 失败, {skipped} 跳过")
    print()

    # 如果有失败，返回非零退出码
    if failed > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
