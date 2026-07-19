"""Git workflow automation for the autopilot system.

Handles branching, committing, and creating pull requests
for autonomous task execution.
"""

from __future__ import annotations

import dataclasses
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclasses.dataclass
class GitCommit:
    message: str
    sha: str | None
    branch: str
    succeeded: bool


@dataclasses.dataclass
class PullRequest:
    title: str
    body: str
    url: str | None
    succeeded: bool


class GitWorkflow:
    """Automate git operations for autopilot task execution."""

    def __init__(self, project_root: str | os.PathLike[str]) -> None:
        self.project_root = Path(project_root).resolve()

    def current_branch(self) -> str | None:
        try:
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip() or None
        except (subprocess.CalledProcessError, FileNotFoundError):
            return None

    def create_branch(self, name: str) -> bool:
        try:
            subprocess.run(["git", "checkout", "-b", name], cwd=self.project_root, check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def stage_all(self) -> bool:
        try:
            subprocess.run(["git", "add", "."], cwd=self.project_root, check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def commit(self, message: str) -> GitCommit:
        branch = self.current_branch()
        sha: str | None = None
        succeeded = False
        try:
            subprocess.run(["git", "add", "."], cwd=self.project_root, check=True, capture_output=True)
            subprocess.run(["git", "commit", "-m", message], cwd=self.project_root, check=True, capture_output=True)
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.project_root,
                check=True,
                capture_output=True,
                text=True,
            )
            sha = result.stdout.strip()
            succeeded = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        return GitCommit(message=message, sha=sha, branch=branch or "unknown", succeeded=succeeded)

    def push(self, remote: str = "origin") -> bool:
        branch = self.current_branch()
        if not branch:
            return False
        try:
            subprocess.run(["git", "push", "-u", remote, branch], cwd=self.project_root, check=True, capture_output=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def create_pull_request(self, title: str, body: str) -> PullRequest:
        branch = self.current_branch()
        url: str | None = None
        succeeded = False
        try:
            cmd = [
                "gh", "pr", "create",
                "--title", title,
                "--body", body,
            ]
            if branch:
                cmd += ["--head", branch]
            result = subprocess.run(cmd, cwd=self.project_root, capture_output=True, text=True, check=True)
            url = result.stdout.strip() or None
            succeeded = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        return PullRequest(title=title, body=body, url=url, succeeded=succeeded)
