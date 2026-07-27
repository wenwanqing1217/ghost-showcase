"""Root test config: disable rate limiter and CSRF, enable header auth for tests."""
import pytest
from unittest.mock import patch


@pytest.fixture(autouse=True)
def _test_security_settings():
    """测试环境配置：禁用限流器和 CSRF，启用 header 认证"""
    with patch("mindflow_map.middleware.rate_limit.settings.rate_limit_disabled", True), \
         patch("mindflow_map.middleware.csrf.settings.csrf_disabled", True), \
         patch("mindflow_map.middleware.auth.settings.allow_header_auth", True):
        yield
