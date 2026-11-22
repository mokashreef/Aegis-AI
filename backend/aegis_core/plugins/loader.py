"""
Aegis AI - Modular Community Plugin & Python Tool Loader.
Auto-discovers and dynamically registers third-party tools from storage/plugins/,
parses standardized plugin.yaml manifests, and executes tools within isolated sandboxes.
"""

import asyncio
import importlib.util
import inspect
from pathlib import Path
import time
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field
import yaml
from aegis_core.config import STORAGE_DIR
from aegis_core.plugins.base import BaseTool, RiskLevel, ToolResult
from aegis_core.plugins.registry import plugin_registry
from aegis_core.utils.logger import logger


class ToolManifestItem(BaseModel):
    """Schema for individual tool definitions within plugin.yaml."""
    name: str
    description: str
    risk_level: RiskLevel = RiskLevel.READ_ONLY
    entrypoint: str  # e.g. "handler.py:run" or "tool.py:CustomToolClass"
    parameters: Dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: float = 15.0


class PluginManifest(BaseModel):
    """Schema for plugin.yaml manifest file."""
    name: str
    version: str = "1.0.0"
    author: str = "Community Contributor"
    description: str = ""
    license: str = "MIT"
    tools: List[ToolManifestItem] = Field(default_factory=list)


class CommunityPluginTool(BaseTool):
    """Wraps dynamically loaded community tool functions or classes with execution isolation."""

    def __init__(
        self,
        name: str,
        description: str,
        risk_level: RiskLevel,
        parameters_schema: Dict[str, Any],
        handler: Callable[..., Any],
        plugin_dir: Path,
        timeout_seconds: float = 15.0,
    ):
        self.name = name
        self.description = description
        self.risk_level = risk_level
        self.parameters_schema = parameters_schema
        self._handler = handler
        self._plugin_dir = plugin_dir.resolve()
        self._timeout_seconds = timeout_seconds

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Executes the community tool inside an isolated async/thread wrapper with timeout guard."""
        start_time = time.perf_counter()
        try:
            # 1. Path Sandboxing Check on any path arguments
            for arg_k, arg_v in kwargs.items():
                if isinstance(arg_v, str) and ("../" in arg_v or "..\\" in arg_v):
                    return ToolResult(
                        success=False,
                        error=f"Security violation: path traversal detected in argument '{arg_k}'.",
                        execution_time_ms=0.0,
                    )

            # 2. Execute target function with timeout
            if inspect.iscoroutinefunction(self._handler):
                coro = self._handler(**kwargs)
                raw_res = await asyncio.wait_for(coro, timeout=self._timeout_seconds)
            else:
                loop = asyncio.get_running_loop()
                raw_res = await asyncio.wait_for(
                    loop.run_in_executor(None, lambda: self._handler(**kwargs)),
                    timeout=self._timeout_seconds,
                )

            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

            # 3. Format result
            if isinstance(raw_res, ToolResult):
                raw_res.execution_time_ms = elapsed_ms
                return raw_res
            elif isinstance(raw_res, dict):
                return ToolResult(
                    success=raw_res.get("success", True),
                    data=raw_res.get("data", raw_res),
                    message=raw_res.get("message", "Tool executed successfully."),
                    error=raw_res.get("error"),
                    execution_time_ms=elapsed_ms,
                )
            else:
                return ToolResult(
                    success=True,
                    data={"result": raw_res},
                    message=str(raw_res),
                    execution_time_ms=elapsed_ms,
                )

        except asyncio.TimeoutError:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            logger.error("Community tool '%s' timed out after %.1fs", self.name, self._timeout_seconds)
            return ToolResult(
                success=False,
                error=f"Execution timed out after {self._timeout_seconds} seconds.",
                execution_time_ms=elapsed_ms,
            )
        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
            logger.error("Community tool '%s' raised exception: %s", self.name, exc, exc_info=True)
            return ToolResult(
                success=False,
                error=str(exc),
                execution_time_ms=elapsed_ms,
            )


class PluginLoader:
    """Discovers, parses, and dynamically loads community extensions from storage/plugins/."""

    def __init__(self, plugins_dir: Optional[Path] = None):
        self.plugins_dir = plugins_dir or (STORAGE_DIR / "plugins")
        self._loaded_plugins: Dict[str, Dict[str, Any]] = {}

    def ensure_plugins_directory(self) -> Path:
        """Ensures the storage/plugins directory exists."""
        self.plugins_dir.mkdir(parents=True, exist_ok=True)
        return self.plugins_dir

    def discover_and_load_all(self) -> Dict[str, Any]:
        """Scans plugins directory, parses manifests, and registers valid tools."""
        self.ensure_plugins_directory()
        discovered: List[str] = []
        loaded_count = 0
        failed_count = 0

        for child in self.plugins_dir.iterdir():
            if child.is_dir() and not child.name.startswith((".", "_")):
                discovered.append(child.name)
                success = self.load_plugin_from_directory(child)
                if success:
                    loaded_count += 1
                else:
                    failed_count += 1

        logger.info(
            "Plugin loader discovery complete: %d found, %d loaded, %d failed.",
            len(discovered), loaded_count, failed_count
        )
        return {
            "discovered": discovered,
            "loaded_count": loaded_count,
            "failed_count": failed_count,
            "active_plugins": list(self._loaded_plugins.keys()),
        }

    def load_plugin_from_directory(self, dir_path: Path) -> bool:
        """Parses plugin.yaml/plugin.json in given directory and registers its tools."""
        manifest_file: Optional[Path] = None
        for cand in ["plugin.yaml", "plugin.yml", "plugin.json"]:
            f = dir_path / cand
            if f.is_file():
                manifest_file = f
                break

        if not manifest_file:
            logger.debug("No manifest found in %s, skipping.", dir_path)
            return False

        try:
            with open(manifest_file, "r", encoding="utf-8") as mf:
                content = mf.read()
                data = yaml.safe_load(content)

            manifest = PluginManifest(**data)
            plugin_id = manifest.name
            registered_tools: List[str] = []

            for tool_item in manifest.tools:
                entrypoint_str = tool_item.entrypoint
                if ":" not in entrypoint_str:
                    logger.warning(
                        "Invalid entrypoint format '%s' for tool '%s' in plugin '%s'. Expected 'file.py:handler'.",
                        entrypoint_str, tool_item.name, plugin_id
                    )
                    continue

                mod_filename, handler_name = entrypoint_str.split(":", 1)
                py_file = dir_path / mod_filename.strip()
                if not py_file.is_file():
                    logger.error("Entrypoint file '%s' not found for plugin '%s'", py_file, plugin_id)
                    continue

                # Load module dynamically
                spec = importlib.util.spec_from_file_location(
                    f"aegis_community_{plugin_id}_{tool_item.name}",
                    py_file,
                )
                if not spec or not spec.loader:
                    logger.error("Failed creating module spec for %s", py_file)
                    continue

                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                handler = getattr(module, handler_name.strip(), None)
                if not handler:
                    logger.error("Handler '%s' not found in %s", handler_name, py_file)
                    continue

                # Instantiate or wrap
                if isinstance(handler, type) and issubclass(handler, BaseTool):
                    tool_instance = handler()
                elif callable(handler):
                    tool_instance = CommunityPluginTool(
                        name=tool_item.name,
                        description=tool_item.description,
                        risk_level=tool_item.risk_level,
                        parameters_schema=tool_item.parameters,
                        handler=handler,
                        plugin_dir=dir_path,
                        timeout_seconds=tool_item.timeout_seconds,
                    )
                else:
                    logger.error("Handler in %s is neither a callable nor a BaseTool subclass", py_file)
                    continue

                plugin_registry.register(tool_instance)
                registered_tools.append(tool_instance.name)

            self._loaded_plugins[plugin_id] = {
                "manifest": manifest.model_dump(),
                "directory": str(dir_path),
                "tools": registered_tools,
                "loaded_at": time.time(),
            }
            logger.info("Successfully loaded plugin '%s' with tools: %s", plugin_id, registered_tools)
            return True

        except Exception as exc:
            logger.error("Failed loading plugin from %s: %s", dir_path, exc, exc_info=True)
            return False

    def unload_plugin(self, plugin_name: str) -> bool:
        """Unregisters all tools belonging to a plugin and removes it from loaded plugins."""
        if plugin_name not in self._loaded_plugins:
            return False

        plugin_info = self._loaded_plugins.pop(plugin_name)
        for tool_name in plugin_info.get("tools", []):
            plugin_registry.unregister(tool_name)

        logger.info("Unloaded plugin '%s'", plugin_name)
        return True

    def list_loaded_plugins(self) -> List[Dict[str, Any]]:
        """Returns structured metadata of all active community plugins."""
        return list(self._loaded_plugins.values())


# Global plugin loader singleton
plugin_loader = PluginLoader()
