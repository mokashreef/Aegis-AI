"""
Integration tests for FastAPI REST API endpoints.
"""

import pytest
from httpx import ASGITransport, AsyncClient
from aegis_core.main import create_app


@pytest.mark.asyncio
async def test_health_and_system_endpoints():
    """Verify /api/health and /api/system/status return healthy statuses."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Health
        health_res = await client.get("/api/health")
        assert health_res.status_code == 200
        health_data = health_res.json()
        assert health_data["status"] == "healthy"
        assert health_data["zero_api_keys_enforced"] is True

        # 2. System Status
        status_res = await client.get("/api/system/status")
        assert status_res.status_code == 200
        status_data = status_res.json()
        assert "telemetry" in status_data
        assert "ai_runtime" in status_data
        assert "voice" in status_data

        # 3. Tool Listing
        tools_res = await client.get("/api/tools")
        assert tools_res.status_code == 200
        tools = tools_res.json()
        assert isinstance(tools, list)


@pytest.mark.asyncio
async def test_session_lifecycle_api():
    """Verify session creation and message query API."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create session
        create_res = await client.post("/api/sessions", params={"title": "API Test Session"})
        assert create_res.status_code == 200
        session_id = create_res.json()["session_id"]
        assert session_id is not None

        # Fetch sessions
        list_res = await client.get("/api/sessions")
        assert list_res.status_code == 200
        sessions = list_res.json()
        assert any(s["id"] == session_id for s in sessions)

