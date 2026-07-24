"""GitHub multi-repo sync script.

Usage:
    python scripts/github_sync.py

Function:
    1. Check network connectivity (proxy-aware)
    2. Iterate through all sub-projects
    3. Auto add / commit / push for repos with changes
    4. Summary output
"""

import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# Repo list (relative path, GitHub remote)
REPOS = [
    ("alphaid", "wenwanqing1217/alpha-id"),
    ("core", "wenwanqing1217/zcode-brain"),
    ("flow", "wenwanqing1217/mindflow"),
    ("nebula", "wenwanqing1217/mindflow-map"),
]

WORKSPACE = Path(__file__).resolve().parent.parent


def run(cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    """Run command, return (returncode, stdout, stderr)."""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        shell=False,
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def check_network() -> bool:
    """Check GitHub connectivity, proxy-aware."""
    code, _, _ = run(["git", "ls-remote", "https://github.com", "HEAD"], WORKSPACE)
    return code == 0


def sync_repo(name: str, remote: str, max_retries: int = 2) -> dict:
    """Sync a single repo with retry."""
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
        result["message"] = "directory not found"
        return result

    code, stdout, stderr = run(["git", "status", "-s"], repo_path)
    if code != 0:
        result["status"] = "error"
        result["message"] = f"git status failed: {stderr}"
        return result

    if not stdout:
        result["status"] = "clean"
        result["message"] = "working tree clean"
        return result

    last_error = ""
    for attempt in range(max_retries):
        if attempt > 0:
            time.sleep(2 ** attempt)

        code, _, stderr = run(["git", "add", "."], repo_path)
        if code != 0:
            last_error = f"git add failed: {stderr}"
            continue

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        commit_msg = f"chore: auto sync {timestamp}"
        code, _, stderr = run(["git", "commit", "-m", commit_msg], repo_path)
        if code != 0:
            last_error = f"git commit failed: {stderr}"
            continue

        code, stdout, stderr = run(["git", "push"], repo_path)
        if code != 0:
            last_error = f"git push failed: {stderr}"
            continue

        code, stdout, _ = run(["git", "log", "-1", "--oneline"], repo_path)
        result["status"] = "pushed"
        result["message"] = stdout or "pushed"
        result["commits"] = 1
        return result

    result["status"] = "error"
    result["message"] = f"{last_error} (retried {max_retries}x)"
    return result


def main():
    print("=" * 60)
    print("  Ghost GitHub Multi-Repo Sync")
    print("=" * 60)
    print()

    print("[*] Checking GitHub connectivity...")
    if not check_network():
        print("[!] Network unreachable, skipping sync")
        sys.exit(0)
    print("[OK] Network ready")
    print()

    results = []
    for name, remote in REPOS:
        print(f"[*] Syncing {name} ({remote}) ...")
        result = sync_repo(name, remote)
        results.append(result)

        if result["status"] == "pushed":
            print(f"    -> pushed: {result['message']}")
        elif result["status"] == "clean":
            print(f"    -> clean")
        elif result["status"] == "skip":
            print(f"    -> skip: {result['message']}")
        else:
            print(f"    -> failed: {result['message']}")

    print()
    print("=" * 60)
    print("  Summary")
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
    print(f"  Total: {pushed} pushed, {clean} clean, {failed} failed, {skipped} skipped")
    print()

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
