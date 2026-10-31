# Dynamic Plugin Subsystem Specification

Aegis AI features an extensible, modular plugin architecture designed to allow developers and community contributors to write custom automation tools in standard Python.

---

## 1. The `BaseTool` Protocol

Every plugin tool inherits from `BaseTool` defined in `aegis_core.plugins.base`:

```python
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict
from pydantic import BaseModel

class RiskLevel(str, Enum):
    READ_ONLY = "read_only"
    MUTATING_SAFE = "mutating_safe"
    RESTRICTED_CONFIRM = "restricted_confirm"

class BaseTool(ABC):
    name: str
    description: str
    risk_level: RiskLevel = RiskLevel.READ_ONLY
    parameters_schema: Dict[str, Any]

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """Executes the tool with validated arguments and returns a dictionary payload."""
        pass
```

---

## 2. Plugin Discovery and Lifecycle

1. **Auto-Discovery**: At daemon boot, `PluginRegistry` scans the `plugins/` directory for Python modules.
2. **Schema Generation**: Each tool's parameter specification is converted to standard JSON Schema compatible with LLM function-calling protocols (OpenAI, Ollama, etc.).
3. **Execution Guardrails**: The executor checks the `risk_level` before running `execute()`.
4. **Error Isolation**: Plugin crashes or exceptions are intercepted, wrapped in structured JSON error responses, and fed back to the agent planner without crashing the main daemon.

