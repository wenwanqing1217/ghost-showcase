"""MindFlow Map 集成测试"""

from fastapi.testclient import TestClient

from mindflow_map.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_workflow_templates():
    response = client.get("/api/v1/workflow/templates")
    assert response.status_code == 200
    data = response.json()
    assert "templates" in data


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "MindFlow Map"
