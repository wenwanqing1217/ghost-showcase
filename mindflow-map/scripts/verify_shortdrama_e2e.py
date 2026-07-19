"""End-to-end verification for the shortdrama automation pipeline.

This script uses FastAPI TestClient to exercise the full flow:
  1. AI scan + submit to review queue
  2. List jobs
  3. Query a job
  4. Approve a job
  5. Reject a job
  6. Copy upload info to clipboard
"""

import os
import sys

# Ensure the src package is importable from this script.
_AID_SRC = os.path.join(os.path.dirname(__file__), "AID", "projects", "src")
if _AID_SRC not in sys.path:
    sys.path.insert(0, _AID_SRC)

# Provide the auth master key expected by the FastAPI lifespan.
os.environ.setdefault("AUTH_MASTER_KEY", "test-master-key-256bit-secret-for-verification-only")

from fastapi.testclient import TestClient

from main import app


def main() -> int:
    client = TestClient(app)

    print("=" * 60)
    print("ShortDrama Automation Pipeline Verification")
    print("=" * 60)

    # Health check
    health = client.get("/health")
    print(f"\n[health] {health.status_code} -> {health.text}")
    assert health.status_code == 200, health.text

    # Submit a job via AI scan + submit
    payload = {
        "title": "测试短剧A",
        "content": "这是一个用于端到端验证的短剧内容。",
        "content_type": "video",
        "user_id": "default",
    }
    submit = client.post("/api/v1/shortdrama/scan-and-submit", json=payload)
    print(f"\n[scan-and-submit] {submit.status_code}")
    print(submit.text)
    assert submit.status_code == 200, submit.text
    job = submit.json()
    job_id = job["job_id"]

    # List jobs
    jobs = client.get("/api/v1/shortdrama/jobs")
    print(f"\n[jobs] {jobs.status_code}")
    print(jobs.text)
    assert jobs.status_code == 200, jobs.text

    # Query single job
    query = client.post("/api/v1/shortdrama/query", json={"job_id": job_id})
    print(f"\n[query] {query.status_code}")
    print(query.text)
    assert query.status_code == 200, query.text

    # Approve job
    approve = client.post("/api/v1/shortdrama/approve", json={"job_id": job_id, "reviewer": "admin"})
    print(f"\n[approve] {approve.status_code}")
    print(approve.text)
    assert approve.status_code == 200, approve.text

    # Reject a second job
    payload["title"] = "测试短剧B"
    payload["content"] = "这是第二个用于端到端验证的短剧内容。"
    submit2 = client.post("/api/v1/shortdrama/scan-and-submit", json=payload)
    assert submit2.status_code == 200, submit2.text
    job2 = submit2.json()
    reject = client.post("/api/v1/shortdrama/reject", json={"job_id": job2["job_id"], "reason": "需要修改内容", "reviewer": "admin"})
    print(f"\n[reject] {reject.status_code}")
    print(reject.text)
    assert reject.status_code == 200, reject.text

    # Copy upload info
    copy = client.post("/api/v1/shortdrama/copy-upload-info", json={"job_id": job_id})
    print(f"\n[copy-upload-info] {copy.status_code}")
    print(copy.text)
    assert copy.status_code == 200, copy.text

    print("\n" + "=" * 60)
    print("Verification passed.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
