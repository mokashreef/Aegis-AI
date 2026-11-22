"""
Aegis AI - Unit Tests for Community Plugins & Modular Python Tools Loader.
Verifies plugin.yaml manifest parsing, auto-discovery from storage/plugins/,
security sandboxing (path traversal & timeouts), and REST API endpoints (resolving Issue #5).
"""

from pathlib import Path
from fastapi.testclient import TestClient
import pytest
from aegis_core.config import STORAGE_DIR
from aegis_core.main import app
from aegis_core.plugins.base import RiskLevel
from aegis_core.plugins.loader import (
    CommunityPluginTool,
    PluginLoader,
    PluginManifest,
    plugin_loader,
)
from aegis_core.plugins.registry import plugin_registry


def test_plugin_manifest_validation():
    sample_yaml = """
    name: test_calc
    version: "1.2.0"
    author: "Test Engineer"
    description: "Calculator plugin"
    tools:
      - name: add_numbers
        description: "Adds two numbers"
        risk_level: "read_only"
        entrypoint: "calc.py:add"
        timeout_seconds: 5.0
        parameters:
          type: object
          properties:
            x:
              type: number
            y:
              type: number
    """
    import yaml

    data = yaml.safe_load(sample_yaml)
    manifest = PluginManifest(**data)
    assert manifest.name == "test_calc"
    assert manifest.version == "1.2.0"
    assert len(manifest.tools) == 1
    assert manifest.tools[0].name == "add_numbers"
    assert manifest.tools[0].risk_level == RiskLevel.READ_ONLY


@pytest.mark.asyncio
async def test_community_plugin_tool_execution():
    def mock_handler(query: str, multiplier: int = 2):
        return f"Echo: {query} x {multiplier}"

    tool = CommunityPluginTool(
        name="mock_echo_tool",
        description="Echoes query",
        risk_level=RiskLevel.READ_ONLY,
        parameters_schema={"type": "object"},
        handler=mock_handler,
        plugin_dir=Path("."),
        timeout_seconds=5.0,
    )

    res = await tool.execute(query="Aegis AI", multiplier=3)
    assert res.success is True
    assert "Aegis AI x 3" in res.message
    assert res.execution_time_ms >= 0.0


@pytest.mark.asyncio
async def test_security_sandboxing_path_traversal():
    def dummy_handler(path: str):
        return "success"

    tool = CommunityPluginTool(
        name="secure_tool",
        description="Path testing",
        risk_level=RiskLevel.READ_ONLY,
        parameters_schema={"type": "object"},
        handler=dummy_handler,
        plugin_dir=Path("."),
    )

    # Path traversal attack attempt
    res = await tool.execute(path="../../system32/config/SAM")
    assert res.success is False
    assert "path traversal detected" in res.error.lower()


@pytest.mark.asyncio
async def test_security_sandboxing_timeout():
    def slow_handler():
        import time
        time.sleep(1.0)
        return "finished"

    tool = CommunityPluginTool(
        name="slow_tool",
        description="Slow testing",
        risk_level=RiskLevel.READ_ONLY,
        parameters_schema={},
        handler=slow_handler,
        plugin_dir=Path("."),
        timeout_seconds=0.1,  # Strict timeout
    )

    res = await tool.execute()
    assert res.success is False
    assert "timed out" in res.error.lower()


def test_load_weather_forecast_community_plugin():
    weather_dir = STORAGE_DIR / "plugins" / "weather_forecast"
    assert weather_dir.exists()

    loader = PluginLoader(plugins_dir=STORAGE_DIR / "plugins")
    success = loader.load_plugin_from_directory(weather_dir)
    assert success is True

    # Verify tool is registered in global registry
    tool = plugin_registry.get("get_weather_forecast")
    assert tool is not None
    assert "weather" in tool.description.lower()

    # Verify list_loaded_plugins
    loaded = loader.list_loaded_plugins()
    assert len(loaded) >= 1
    assert any(p["manifest"]["name"] == "weather_forecast" for p in loaded)

    # Test unloading
    unloaded = loader.unload_plugin("weather_forecast")
    assert unloaded is True
    assert plugin_registry.get("get_weather_forecast") is None

    # Reload back for system availability
    loader.load_plugin_from_directory(weather_dir)
    assert plugin_registry.get("get_weather_forecast") is not None


@pytest.mark.asyncio
async def test_execute_weather_forecast_tool():
    weather_dir = STORAGE_DIR / "plugins" / "weather_forecast"
    plugin_loader.load_plugin_from_directory(weather_dir)

    tool = plugin_registry.get("get_weather_forecast")
    assert tool is not None

    res = await tool.execute(city="عمان")
    assert res.success is True
    assert "عمان" in res.message
    assert "temperature_celsius" in res.data


def test_plugin_rest_api_endpoints():
    client = TestClient(app)

    # 1. GET /api/plugins
    resp = client.get("/api/plugins")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_tools" in data
    assert "tools" in data
    assert "community_plugins" in data
    assert data["total_tools"] > 0

    # 2. POST /api/plugins/reload
    reload_resp = client.post("/api/plugins/reload")
    assert reload_resp.status_code == 200
    r_data = reload_resp.json()
    assert r_data["success"] is True
    assert "discovery_status" in r_data
