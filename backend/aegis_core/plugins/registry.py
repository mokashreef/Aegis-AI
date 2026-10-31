"""
Aegis AI - Dynamic Plugin Registry & Dispatcher.
"""

import time
from typing import Any, Dict, List, Optional
from aegis_core.plugins.base import BaseTool, RiskLevel, ToolResult
from aegis_core.utils.logger import logger


class PluginRegistry:
    """Registry maintaining registered tools and executing them with safety policies."""

    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        """Registers an instance of BaseTool."""
        if tool.name in self._tools:
            logger.warning("Overwriting already registered tool '%s'", tool.name)
        self._tools[tool.name] = tool
        logger.debug("Registered tool: %s (Risk: %s)", tool.name, tool.risk_level.value)

    def unregister(self, tool_name: str) -> None:
        """Removes a tool from the registry."""
        if tool_name in self._tools:
            del self._tools[tool_name]
            logger.debug("Unregistered tool: %s", tool_name)

    def get(self, tool_name: str) -> Optional[BaseTool]:
        """Retrieves a registered tool by name."""
        return self._tools.get(tool_name)

    def list_tools(self) -> List[Dict[str, Any]]:
        """Returns metadata for all registered tools."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "risk_level": tool.risk_level.value,
                "parameters": tool.parameters_schema,
            }
            for tool in self._tools.values()
        ]

    def get_function_schemas(self) -> List[Dict[str, Any]]:
        """Returns tool definitions formatted for LLM consumption."""
        return [tool.get_tool_definition() for tool in self._tools.values()]

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        user_confirmed: bool = False,
    ) -> ToolResult:
        """Executes a tool by name with safety checks and performance measurement."""
        tool = self.get(tool_name)
        if not tool:
            return ToolResult(
                success=False,
                error=f"Tool '{tool_name}' is not registered in Aegis AI.",
            )

        # Risk Interception Gate
        if tool.risk_level == RiskLevel.RESTRICTED_CONFIRM and not user_confirmed:
            return ToolResult(
                success=False,
                error=f"Execution of '{tool_name}' requires explicit user confirmation.",
                data={"requires_confirmation": True, "tool_name": tool_name, "arguments": arguments},
            )

        start_time = time.perf_counter()
        try:
            result = await tool.execute(**arguments)
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            result.execution_time_ms = round(elapsed_ms, 2)
            return result
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            logger.error("Error executing tool '%s': %s", tool_name, exc, exc_info=True)
            return ToolResult(
                success=False,
                error=str(exc),
                execution_time_ms=round(elapsed_ms, 2),
            )


# Global plugin registry singleton
plugin_registry = PluginRegistry()

