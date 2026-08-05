"""API 一致性检查：响应格式、OpenAPI Schema、版本控制。"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mindflow_map.api.openapi_config import custom_openapi
from mindflow_map.main import app as _app


@pytest.fixture()
def client() -> TestClient:
    """同步测试客户端。"""
    return TestClient(_app)


class TestApiResponseConsistency:
    """验证所有 API 端点响应格式一致。"""

    def test_health_endpoints_return_success_flag(self, client: TestClient) -> None:
        """health 端点应返回 success=True 或标准结构。"""
        for path in ("/health", "/health/livez", "/health/readyz", "/health/healthz"):
            response = client.get(path)
            assert response.status_code == 200, f"{path} failed: {response.status_code}"
            # 至少应包含 status 或 success 字段
            body = response.json()
            assert "status" in body or "success" in body, f"{path} missing status/success"

    def test_root_returns_basic_info(self, client: TestClient) -> None:
        response = client.get("/")
        assert response.status_code == 200
        body = response.json()
        assert "name" in body
        assert "version" in body
        assert "status" in body


class TestOpenapiSchema:
    """验证 OpenAPI Schema 完整性。"""

    @pytest.fixture()
    def openapi_schema(self) -> dict:
        schema = custom_openapi(_app)
        return schema

    def test_has_api_version(self, openapi_schema: dict) -> None:
        assert openapi_schema["info"]["x-api-version"] == "v1"

    def test_has_security_schemes(self, openapi_schema: dict) -> None:
        schemes = openapi_schema["components"]["securitySchemes"]
        assert "BearerAuth" in schemes
        assert "TenantAuth" in schemes

    def test_has_server_urls(self, openapi_schema: dict) -> None:
        servers = openapi_schema.get("servers", [])
        assert len(servers) >= 1

    def test_health_paths_excluded_from_security(self, openapi_schema: dict) -> None:
        paths = openapi_schema.get("paths", {})
        for path in paths:
            if path.startswith("/health"):
                for method_info in paths[path].values():
                    if isinstance(method_info, dict):
                        assert "security" not in method_info, f"{path} should not require auth"

    def test_has_tag_descriptions(self, openapi_schema: dict) -> None:
        tags = openapi_schema.get("tags", [])
        assert len(tags) >= 5
        for tag in tags:
            assert "description" in tag
            assert len(tag["description"]) > 0

    def test_has_response_examples(self, openapi_schema: dict) -> None:
        examples = openapi_schema.get("components", {}).get("examples", {})
        assert "SuccessResponse" in examples
        assert "ErrorResponse" in examples


class TestApiVersioning:
    """验证 API 版本控制策略。"""

    def test_all_business_routes_have_v1_prefix(self) -> None:
        schema = custom_openapi(_app)
        paths = list(schema.get("paths", {}).keys())
        business_paths = [
            p for p in paths
            if p.startswith("/api/") and not p.startswith("/api/v1/")
        ]
        assert len(business_paths) == 0, f"Found non-v1 business paths: {business_paths}"

    def test_health_routes_are_unversioned(self) -> None:
        schema = custom_openapi(_app)
        paths = list(schema.get("paths", {}).keys())
        health_paths = [p for p in paths if p.startswith("/health")]
        assert len(health_paths) >= 1


class TestResponseFormat:
    """验证响应包装一致性。"""

    def test_error_handlers_register_standard_format(self, client: TestClient) -> None:
        """触发 404 应返回标准错误格式。"""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404
        body = response.json()
        # 统一错误处理器应包含 error/message/detail
        assert "error" in body or "detail" in body


class TestSdkGenerationDoc:
    """验证 SDK 生成文档存在且可读。"""

    def test_sdk_doc_exists(self) -> None:
        doc_path = Path(__file__).resolve().parent.parent.parent / "docs" / "OPENAPI_SDK_GENERATION.md"
        assert doc_path.exists(), f"SDK generation doc not found at {doc_path}"
        content = doc_path.read_text(encoding="utf-8")
        assert "OpenAPI" in content
        assert "openapi-generator" in content

    def test_api_versioning_doc_exists(self) -> None:
        doc_path = Path(__file__).resolve().parent.parent.parent / "docs" / "API_VERSIONING.md"
        assert doc_path.exists(), f"API versioning doc not found at {doc_path}"
        content = doc_path.read_text(encoding="utf-8")
        assert "v1" in content
        assert "v2" in content
