"""
End-to-end tests — full chain through Gateway to real services.

These tests verify the complete request path:
  Client → Gateway (:18080) → Backend service

Covers:
  - Gateway health aggregates all backend statuses
  - Flow proxy: templates, execute, executions
  - Flow proxy: AID session lifecycle
  - Flow proxy: map search, routes
  - Flow proxy: computer-use status
  - Alpha-ID proxy: identity endpoints
  - Net-Agent proxy: vendors endpoint
  - Correlation ID propagation
  - Error handling for invalid routes
"""


# ── Gateway Health ──


class TestGatewayHealth:
    """Gateway /health aggregates all backend statuses."""

    def test_health_returns_all_components(self, real_gateway, http_client):
        """Gateway health includes all service statuses."""
        r = http_client.get(f"{real_gateway}/health")
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        components = data["data"]
        assert components["gateway"] == "ok"
        assert "alphaid" in components
        assert "flow" in components
        assert "netagent" in components

    def test_health_includes_request_id(self, real_gateway, http_client):
        """Health response includes X-Request-ID header."""
        r = http_client.get(f"{real_gateway}/health")
        assert "x-request-id" in r.headers

    def test_health_respects_client_request_id(self, real_gateway, http_client):
        """Gateway echoes back client-provided X-Request-ID."""
        custom_id = "e2e-health-001"
        r = http_client.get(
            f"{real_gateway}/health",
            headers={"X-Request-ID": custom_id},
        )
        assert r.headers["x-request-id"] == custom_id


# ── Flow Proxy — Workflows ──


class TestFlowWorkflowProxy:
    """Gateway proxies workflow endpoints to Flow service."""

    def test_flow_health_via_gateway(self, real_gateway, http_client):
        """GET /v1/agent/flow/health returns Flow service status."""
        r = http_client.get(f"{real_gateway}/v1/agent/flow/health")
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert data["data"]["status"] == "ok"

    def test_flow_templates_via_gateway(self, real_gateway, http_client):
        """GET /v1/agent/flow/templates returns template list."""
        r = http_client.get(f"{real_gateway}/v1/agent/flow/templates")
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        # Flow returns templates as a direct array
        assert isinstance(data["data"], list)
        assert len(data["data"]) > 0

    def test_flow_template_by_id_via_gateway(self, real_gateway, http_client):
        """GET /v1/agent/flow/templates/:id returns single template."""
        r = http_client.get(f"{real_gateway}/v1/agent/flow/templates/tpl-greeting")
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert data["data"]["id"] == "tpl-greeting"

    def test_flow_execute_via_gateway(self, real_gateway, http_client):
        """POST /v1/agent/flow/execute runs a workflow."""
        r = http_client.post(
            f"{real_gateway}/v1/agent/flow/execute",
            json={"message": "search for AI news"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        # Flow returns executionId (camelCase)
        assert "executionId" in data["data"]

    def test_flow_execute_unmatched_returns_error(self, real_gateway, http_client):
        """POST /v1/agent/flow/execute returns error for unmatched messages."""
        r = http_client.post(
            f"{real_gateway}/v1/agent/flow/execute",
            json={"message": "xyzqwerty12345"},
        )
        # Flow returns 404, Gateway wraps as 502
        assert r.status_code in [404, 502]

    def test_flow_executions_via_gateway(self, real_gateway, http_client):
        """GET /v1/agent/flow/executions returns execution list."""
        r = http_client.get(f"{real_gateway}/v1/agent/flow/executions")
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        # Flow returns executions as a direct array
        assert isinstance(data["data"], list)


# ── Flow Proxy — AID Sessions ──


class TestFlowAIDProxy:
    """Gateway proxies AID session endpoints to Flow service."""

    def test_aid_capabilities_via_gateway(self, real_gateway, http_client):
        """GET /v1/agent/flow/aid/capabilities returns agent capabilities."""
        r = http_client.get(f"{real_gateway}/v1/agent/flow/aid/capabilities")
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True

    def test_aid_session_lifecycle(self, real_gateway, http_client):
        """Full AID session lifecycle: create → message → get → delete."""
        # Create session
        r = http_client.post(
            f"{real_gateway}/v1/agent/flow/aid/sessions",
            json={"context": "e2e test"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        # Flow returns session with 'id' field (not 'session_id')
        session_id = data["data"]["id"]
        assert session_id

        # Send message (Flow expects { message } not { role, content })
        r = http_client.post(
            f"{real_gateway}/v1/agent/flow/aid/sessions/{session_id}/messages",
            json={"message": "Hello"},
        )
        assert r.status_code == 200

        # Get session
        r = http_client.get(f"{real_gateway}/v1/agent/flow/aid/sessions/{session_id}")
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True

        # Delete session
        r = http_client.delete(
            f"{real_gateway}/v1/agent/flow/aid/sessions/{session_id}"
        )
        assert r.status_code == 200


# ── Flow Proxy — Map ──


class TestFlowMapProxy:
    """Gateway proxies map endpoints to Flow service."""

    def test_map_search_via_gateway(self, real_gateway, http_client):
        """GET /v1/agent/flow/map/search returns POI results."""
        r = http_client.get(
            f"{real_gateway}/v1/agent/flow/map/search",
            params={"q": "Beijing"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True

    def test_map_pois_via_gateway(self, real_gateway, http_client):
        """GET /v1/agent/flow/map/pois returns POI list."""
        r = http_client.get(f"{real_gateway}/v1/agent/flow/map/pois")
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True

    def test_map_route_lifecycle(self, real_gateway, http_client):
        """Full route lifecycle: create → list → get → delete."""
        # Create route (requires name + at least 2 points)
        r = http_client.post(
            f"{real_gateway}/v1/agent/flow/map/routes",
            json={
                "name": "E2E Test Route",
                "points": [
                    {"name": "Beijing", "lat": 39.9, "lon": 116.4},
                    {"name": "Shanghai", "lat": 31.2, "lon": 121.5},
                ],
            },
        )
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        # Flow returns route with 'id' field (not 'route_id')
        route_id = data["data"]["id"]
        assert route_id

        # List routes
        r = http_client.get(f"{real_gateway}/v1/agent/flow/map/routes")
        assert r.status_code == 200

        # Get route
        r = http_client.get(f"{real_gateway}/v1/agent/flow/map/routes/{route_id}")
        assert r.status_code == 200

        # Delete route
        r = http_client.delete(f"{real_gateway}/v1/agent/flow/map/routes/{route_id}")
        assert r.status_code == 200


# ── Flow Proxy — Computer Use ──


class TestFlowComputerUseProxy:
    """Gateway proxies computer-use endpoints to Flow service."""

    def test_computer_use_status_via_gateway(self, real_gateway, http_client):
        """GET /v1/agent/flow/computer-use/status returns agent status."""
        r = http_client.get(f"{real_gateway}/v1/agent/flow/computer-use/status")
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True

    def test_computer_use_task_lifecycle(self, real_gateway, http_client):
        """Full task lifecycle: create → list → get."""
        # Create task (type must be one of: navigate, screenshot, click, type, extract)
        r = http_client.post(
            f"{real_gateway}/v1/agent/flow/computer-use/tasks",
            json={"type": "navigate", "params": {"url": "https://example.com"}},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        # Flow returns task with 'id' field (not 'task_id')
        task_id = data["data"]["id"]
        assert task_id

        # List tasks
        r = http_client.get(f"{real_gateway}/v1/agent/flow/computer-use/tasks")
        assert r.status_code == 200

        # Get task
        r = http_client.get(
            f"{real_gateway}/v1/agent/flow/computer-use/tasks/{task_id}"
        )
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True


# ── Alpha-ID Proxy ──


class TestAlphaIDProxy:
    """Gateway proxies human endpoints to Alpha-ID service."""

    def test_identity_stats_via_gateway(self, real_gateway, http_client):
        """GET /v1/agent/interact/topology proxies to Alpha-ID stats."""
        r = http_client.get(f"{real_gateway}/v1/agent/interact/topology")
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True


# ── Net-Agent Proxy ──


class TestNetAgentProxy:
    """Gateway proxies net routes to Net-Agent service."""

    def test_net_vendors_via_gateway(self, real_gateway, http_client):
        """GET /v1/net/vendors proxies to Net-Agent."""
        r = http_client.get(f"{real_gateway}/v1/net/vendors")
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True


# ── Error Handling ──


class TestErrorHandling:
    """Gateway handles errors gracefully."""

    def test_invalid_route_returns_404(self, real_gateway, http_client):
        """Unknown route returns 404 with error envelope."""
        r = http_client.get(f"{real_gateway}/v1/nonexistent/route")
        assert r.status_code == 404

    def test_flow_invalid_template_returns_error(self, real_gateway, http_client):
        """Requesting non-existent template returns error."""
        r = http_client.get(f"{real_gateway}/v1/agent/flow/templates/does-not-exist")
        # Should return 404 (from Flow) or 502 (Gateway wrapped)
        assert r.status_code in [404, 502]
