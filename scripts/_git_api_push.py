"""通过 GitHub Git Data API 推送任意本地 commit（绕过被 GFW 封锁的 github.com:443 git 协议）。

用法:
    python _git_api_push.py <owner/repo> <branch> <local_commit> <token> [local_dir]

原理:
1. 取远程 branch 当前 commit/tree（git ls-tree -r 与本地 diff 找出需要上传的 blob）
2. 只上传变更的 blob，基于远程 tree 重建新 tree（与 local_commit 的 tree 逐字节一致）
3. 创建 commit（parent=远程当前 commit，message 取自 git log）→ PATCH ref

要求: 远程 branch 是 local_commit 的祖先（快进更新）。
"""

import base64
import json
import subprocess
import sys
import urllib.request
from datetime import datetime

GIT_DIR = r"d:\MW"


def git(*args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", GIT_DIR, *args], check=True, capture_output=True
    ).stdout


def api(method: str, path: str, payload: dict | None = None) -> dict:
    url = f"https://api.github.com/repos/{REPO}{path}"
    data = None
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "ghost-ci-push",
    }
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as resp:
            body = resp.read()
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        raise SystemExit(f"HTTP {e.code} on {method} {path}: {body}") from e


def main() -> None:
    global REPO, TOKEN, BRANCH, GIT_DIR
    repo_arg, branch, local_commit, token = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    REPO, BRANCH, TOKEN = repo_arg, branch, token
    if len(sys.argv) > 5:
        GIT_DIR = sys.argv[5]

    # 1. 远程当前状态
    ref_info = api("GET", f"/git/refs/heads/{branch}")
    remote_commit = ref_info["object"]["sha"]
    remote_tree = api("GET", f"/git/commits/{remote_commit}")["tree"]["sha"]
    print(f"remote {branch} = {remote_commit} tree={remote_tree}")

    # 2. 本地 commit 的 tree + 变更文件
    local_tree = git("rev-parse", f"{local_commit}^{{tree}}").decode().strip()
    msg = git("log", "-1", "--format=%B", local_commit).decode().strip()
    author = git("log", "-1", "--format=%an <%ae>").decode().strip()
    name, email = author.split(" <")[0], author.split(" <")[1][:-1]
    changed = (
        git("diff", "--name-status", remote_commit, local_commit)
        .decode()
        .strip()
        .splitlines()
    )
    deleted = [ln for ln in changed if ln.startswith("D\t")]
    if deleted:
        raise SystemExit(f"删除文件不支持（Git tree 继承语义）：{deleted}")
    print(f"local commit {local_commit} tree={local_tree}")
    print(f"changed files: {len(changed)}")
    for line in changed:
        print("  ", line)

    # 3. 上传变更文件的 blob
    blob_cache: dict[str, str] = {}

    def upload_blob(path: str) -> str:
        raw = git("cat-file", "blob", f"{local_commit}:{path}")
        b64 = base64.b64encode(raw).decode("ascii")
        sha = api("POST", "/git/blobs", {"content": b64, "encoding": "base64"})["sha"]
        blob_cache[path] = sha
        print(f"  blob {path}: {sha}")
        return sha

    # 4. 递归重建 tree，保持与 local_commit 一致
    def rebuild_tree(tree_sha: str, prefix: str) -> str:
        entries_raw = api("GET", f"/git/trees/{tree_sha}")["tree"]
        new_entries = []
        for e in entries_raw:
            etype = e["type"]
            path = e["path"]
            full = f"{prefix}{path}" if prefix else path
            mode = e["mode"]
            if etype == "tree":
                # 检查该子树内是否有变更
                sub_changed = any(
                    (ln.split("\t", 1)[1].startswith(full + "/"))
                    for ln in changed
                    if "\t" in ln
                )
                if sub_changed:
                    new_sub = rebuild_tree(e["sha"], full + "/")
                    new_entries.append({"mode": mode, "path": path, "sha": new_sub, "type": "tree"})
                else:
                    new_entries.append({"mode": mode, "path": path, "sha": e["sha"], "type": "tree"})
            else:  # blob / commit(submodule) / symlink
                new_entries.append({"mode": mode, "path": path, "sha": e["sha"], "type": etype})
        # 新增/替换 blob：对每个变更文件定位其所在目录层
        for ln in changed:
            if "\t" not in ln:
                continue
            status, p = ln.split("\t", 1)
            if status in ("D",):
                continue  # 删除：跳过该路径（GitHub tree 不支持显式删除，父 tree 重建即不含）
            parts = p.split("/")
            if prefix and not p.startswith(prefix):
                continue
            rel = p[len(prefix):] if prefix else p
            if "/" in rel:
                continue  # 深层文件由子树递归处理
            # 该层直接子文件：检查是否已被子树递归处理过（不可能），直接替换
            if not any(e["path"] == rel for e in new_entries):
                new_entries.append(
                    {"mode": "100644", "path": rel, "sha": upload_blob(p), "type": "blob"}
                )
            else:
                for i, e in enumerate(new_entries):
                    if e["path"] == rel:
                        new_entries[i] = {"mode": e["mode"], "path": rel, "sha": upload_blob(p), "type": e["type"]}
        payload = {"base_tree": tree_sha, "tree": new_entries}
        new_sha = api("POST", "/git/trees", payload)["sha"]
        print(f"  tree {prefix or '(root)'}: {new_sha}")
        return new_sha

    new_root = rebuild_tree(remote_tree, "")

    # 5. commit + ref
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    commit = api(
        "POST",
        "/git/commits",
        {
            "message": msg,
            "tree": new_root,
            "parents": [remote_commit],
            "author": {"name": name, "email": email, "date": now},
            "committer": {"name": name, "email": email, "date": now},
        },
    )["sha"]
    api("PATCH", f"/git/refs/heads/{branch}", {"sha": commit, "force": False})
    print(f"PUSHED {branch} -> {commit}")


if __name__ == "__main__":
    main()
