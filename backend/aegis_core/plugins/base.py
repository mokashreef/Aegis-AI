"""
Aegis AI - Dynamic Plugin & Tool Specification.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    """Safety classification for tool execution."""
    READ_ONLY = "read_only"
    MUTATING_SAFE = "mutating_safe"
    RESTRICTED_CONFIRM = "restricted_confirm"


class ToolResult(BaseModel):
    """Structured response container for all tool executions."""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
        }


class BaseTool(ABC):
    """Abstract base class that all Aegis AI automation tools and plugins must implement."""

    name: str
    description: str
    risk_level: RiskLevel = RiskLevel.READ_ONLY
    parameters_schema: Dict[str, Any] = Field(default_factory=dict)

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Executes the tool with validated arguments and returns a structured ToolResult."""
        pass

    def get_tool_definition(self) -> Dict[str, Any]:
        """Returns standard OpenAI / Ollama compatible function schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema,
            },
        }

