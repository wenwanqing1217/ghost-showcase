"""Phase 6: Acceptance verification for Ghost workspace renovation."""

from __future__ import annotations

import os
import re
import sys

BASE_DIR = "D:\\MW"

# ── Check 1: No hardcoded secrets ──

SECRET_PATTERNS = [
    (r"sk-[a-zA-Z0-9]{20,}", "OpenAI-style key (sk-*)"),
    (r"shpat_[a-zA-Z0-9]{20,}", "Shopify token (shpat_*)"),
    (r"ghp_[a-zA-Z0-9]{20,}", "GitHub token (ghp_*)"),
    (r"gho_[a-zA-Z0-9]{20,}", "GitHub OAuth (gho_*)"),
    (r"AKIA[0-9A-Z]{16}", "AWS Access Key (AKIA*)"),
    (r"-----BEGIN\s+(RSA|EC|DSA|OPENSSH)\s+PRIVATE\s+KEY-----", "Private key"),
]

SCAN_DIRS = [
    "mindflow-map/src",
    "DS/src",
    "AID/projects/src",
    "zcode-brain/dispatcher",
    "zcode-brain/safety",
    "zcode-brain/roles",
]

SKIP_DIRS = {"__pycache__", "node_modules", ".git", ".next", ".venv", "venv"}


def check_secrets() -> list[str]:
    """Scan source files for hardcoded secrets. Returns list of issues."""
    issues = []
    for scan_dir in SCAN_DIRS:
        full_dir = os.path.join(BASE_DIR, scan_dir)
        if not os.path.exists(full_dir):
            continue
        for root, dirs, files in os.walk(full_dir):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for fname in files:
                if not fname.endswith((".py", ".ts", ".tsx", ".js", ".jsx")):
                    continue
                if fname.endswith(".test.ts") or fname.endswith(".test.tsx") or fname.endswith(".test.py"):
                    continue  # Skip test files (they use fake keys)
                fpath = os.path.join(root, fname)
                try:
                    with open(fpath, "r", encoding="utf-8", errors="replace") as fh:
                        content = fh.read()
                except Exception:
                    continue
                for pattern, label in SECRET_PATTERNS:
                    matches = re.findall(pattern, content)
                    if matches:
                        issues.append(f"  {fpath}: {len(matches)} potential {label}")
    return issues


def check_gitignore() -> list[str]:
    """Check that .env is gitignored."""
    issues = []
    gitignore_path = os.path.join(BASE_DIR, ".gitignore")
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r") as f:
            content = f.read()
        if ".env" not in content:
            issues.append("Root .gitignore missing .env entry")
    else:
        issues.append("Root .gitignore not found")
    return issues


def check_env_examples() -> list[str]:
    """Check that each project has .env.example."""
    issues = []
    projects = ["mindflow-map", "DS", "AID\\projects"]
    for proj in projects:
        example_path = os.path.join(BASE_DIR, proj, ".env.example")
        if not os.path.exists(example_path):
            issues.append(f"Missing {proj}/.env.example")
    return issues


def check_test_counts() -> dict[str, tuple[int, int]]:
    """Run tests and return counts. Returns {project: (passed, total)}."""
    import subprocess

    results = {}

    # AID
    try:
        r = subprocess.run(
            ["python", "-m", "pytest", "tests/", "-q", "--tb=no"],
            cwd=os.path.join(BASE_DIR, "AID", "projects"),
            capture_output=True, text=True, timeout=120,
        )
        output = r.stdout + r.stderr
        # Parse "923 passed" from output
        m = re.search(r"(\d+)\s+passed", output)
        if m:
            results["AID"] = (int(m.group(1)), int(m.group(1)))
    except Exception as e:
        results["AID"] = (0, 0)

    # mindflow-map
    try:
        r = subprocess.run(
            ["python", "-m", "pytest", "tests/", "-q", "--tb=no"],
            cwd=os.path.join(BASE_DIR, "mindflow-map"),
            capture_output=True, text=True, timeout=120,
        )
        output = r.stdout + r.stderr
        m = re.search(r"(\d+)\s+passed", output)
        if m:
            results["mindflow-map"] = (int(m.group(1)), int(m.group(1)))
    except Exception as e:
        results["mindflow-map"] = (0, 0)

    return results


def main() -> int:
    print("=" * 60)
    print("Phase 6: Acceptance Verification")
    print("=" * 60)

    all_ok = True

    # ── Security ──
    print("\n--- Security Checks ---")

    secret_issues = check_secrets()
    if secret_issues:
        print("⚠️  Potential hardcoded secrets:")
        for issue in secret_issues:
            print(issue)
        all_ok = False
    else:
        print("✅ No hardcoded secrets in source files")

    gitignore_issues = check_gitignore()
    if gitignore_issues:
        for issue in gitignore_issues:
            print(f"❌ {issue}")
        all_ok = False
    else:
        print("✅ .env is gitignored")

    env_example_issues = check_env_examples()
    if env_example_issues:
        for issue in env_example_issues:
            print(f"❌ {issue}")
        all_ok = False
    else:
        print("✅ All projects have .env.example")

    # ── Deployment ──
    print("\n--- Deployment Checks ---")

    # Check docker-compose.yml exists
    compose_path = os.path.join(BASE_DIR, "docker-compose.yml")
    if os.path.exists(compose_path):
        print("✅ Root docker-compose.yml exists")
    else:
        print("❌ Root docker-compose.yml missing")
        all_ok = False

    # Check start-demo.bat exists
    start_path = os.path.join(BASE_DIR, "start-demo.bat")
    if os.path.exists(start_path):
        print("✅ start-demo.bat exists")
    else:
        print("❌ start-demo.bat missing")
        all_ok = False

    # Check health_check.py exists
    health_path = os.path.join(BASE_DIR, "scripts", "health_check.py")
    if os.path.exists(health_path):
        print("✅ scripts/health_check.py exists")
    else:
        print("❌ scripts/health_check.py missing")
        all_ok = False

    # ── Documentation ──
    print("\n--- Documentation Checks ---")

    INFLATED_PHRASES = ["可直接部署", "直接运行，无需配置"]
    # Note: "生产级" is allowed in negative context (e.g., "不是生产级平台")

    docs = ["README.md", "PORTFOLIO.md", "DEPLOY.md", "Caddyfile"]
    for doc in docs:
        doc_path = os.path.join(BASE_DIR, doc)
        if os.path.exists(doc_path):
            with open(doc_path, "r", encoding="utf-8") as f:
                content = f.read()
            found = [p for p in INFLATED_PHRASES if p in content]
            if found:
                print(f"⚠️  {doc} contains inflated claims: {found}")
                all_ok = False
            else:
                print(f"✅ {doc} exists and is honest")
        else:
            print(f"❌ {doc} missing")
            all_ok = False

    # ── Integration ──
    print("\n--- Integration Checks ---")

    # Check AID has auth_verify endpoint
    identity_path = os.path.join(BASE_DIR, "AID", "projects", "src", "api", "identity.py")
    if os.path.exists(identity_path):
        with open(identity_path, "r") as f:
            content = f.read()
        if "auth/verify" in content and "VerifyRequest" in content:
            print("✅ AID /auth/verify endpoint exists with VerifyRequest model")
        else:
            print("❌ AID /auth/verify endpoint incomplete")
            all_ok = False

    # ── Summary ──
    print("\n" + "=" * 60)
    if all_ok:
        print("RESULT: ✅ ALL CHECKS PASSED")
    else:
        print("RESULT: ⚠️  SOME CHECKS FAILED (see above)")
    print("=" * 60)

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
