"""
Unit tests for the dynamic plugin registry and BaseTool interface.
"""

import pytest
from aegis_core.plugins.base import BaseTool, RiskLevel, ToolResult
from aegis_core.plugins.registry import PluginRegistry


class MockSafeTool(BaseTool):
    name = "mock_safe"
    description = "A mock safe tool for unit tests"
    risk_level = RiskLevel.READ_ONLY
    parameters_schema = {"type": "object", "properties": {"value": {"type": "string"}}}

    async def execute(self, value: str = "default", **kwargs) -> ToolResult:
        return ToolResult(success=True, data={"echo": value})


class MockDangerousTool(BaseTool):
    name = "mock_dangerous"
    description = "A mock restricted tool requiring confirmation"
    risk_level = RiskLevel.RESTRICTED_CONFIRM
    parameters_schema = {"type": "object", "properties": {}}

    async def execute(self, **kwargs) -> ToolResult:
        return ToolResult(success=True, data={"deleted": True})


@pytest.mark.asyncio
async def test_plugin_registry_lifecycle():
    registry = PluginRegistry()
    tool = MockSafeTool()

    # Registration
    registry.register(tool)
    assert registry.get("mock_safe") is not None
    assert len(registry.list_tools()) == 1

    # Execution
    res = await registry.execute_tool("mock_safe", {"value": "test_token"})
    assert res.success is True
    assert res.data["echo"] == "test_token"
    assert res.execution_time_ms >= 0.0

    # Unregistration
    registry.unregister("mock_safe")
    assert registry.get("mock_safe") is None


@pytest.mark.asyncio
async def test_plugin_registry_risk_interception():
    registry = PluginRegistry()
    danger_tool = MockDangerousTool()
    registry.register(danger_tool)

    # 1. Without confirmation: should be blocked
    res_blocked = await registry.execute_tool("mock_dangerous", {}, user_confirmed=False)
    assert res_blocked.success is False
    assert "requires explicit user confirmation" in (res_blocked.error or "")

    # 2. With confirmation: should execute
    res_allowed = await registry.execute_tool("mock_dangerous", {}, user_confirmed=True)
    assert res_allowed.success is True
    assert res_allowed.data["deleted"] is True
