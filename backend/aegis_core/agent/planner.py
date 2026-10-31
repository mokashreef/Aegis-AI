"""
Aegis AI - ReAct Agent Planner & Multi-Step Reasoning Engine.
Coordinates system prompts, tool selection, observation feedback, and self-correction.
"""

import json
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional
from aegis_core.ai_runtime.base import LLMMessage
from aegis_core.ai_runtime.router import AIRuntimeRouter, ai_router
from aegis_core.memory.session_manager import SessionManager, session_manager
from aegis_core.plugins.registry import PluginRegistry, plugin_registry
from aegis_core.utils.logger import logger

SYSTEM_PROMPT = """You are Aegis AI, the official open-source, local-first Windows AI companion.
You live on the user's desktop, floating seamlessly above their workspace.

CORE OPERATIONAL PRINCIPLES:
1. Native Windows Helper: You can launch desktop applications, inspect running processes,
   interact with the system clipboard, and monitor Windows telemetry.
2. Direct and Helpful: Be concise, clear, and proactive.
3. Tool Usage: When the user asks you to interact with Windows (e.g., open an app, read
   clipboard, list processes), use your registered tools.
4. Tool Format:
   If you need to call a tool, respond with a JSON block:
   ```tool_call
   {
     "name": "tool_name",
     "arguments": {"param1": "val1"}
   }
   ```
5. Safety: Never attempt destructive actions without warning the user.
"""


class AgentPlanner:
    """Executes multi-step reasoning and tool dispatch."""

    def __init__(
        self,
        router: Optional[AIRuntimeRouter] = None,
        registry: Optional[PluginRegistry] = None,
        memory: Optional[SessionManager] = None,
    ):
        self.router = router or ai_router
        self.registry = registry or plugin_registry
        self.memory = memory or session_manager

    def _extract_tool_call(self, text: str) -> Optional[Dict[str, Any]]:
        """Parses tool calls from markdown tool_call code blocks or JSON."""
        if "```tool_call" in text:
            try:
                start = text.index("```tool_call") + len("```tool_call")
                end = text.index("```", start)
                raw_json = text[start:end].strip()
                return json.loads(raw_json)
            except Exception as exc:
                logger.debug("Failed parsing tool_call block: %s", exc)

        # Fallback keyword matching for quick direct commands
        text_lower = text.strip().lower()
        if text_lower.startswith("open ") or text_lower.startswith("launch "):
            app = text.strip().split(" ", 1)[1].strip()
            # If user said 'open notepad', map to launch_application
            return {"name": "launch_application", "arguments": {"app_name": app}}
        elif text_lower == "get clipboard" or text_lower == "read clipboard":
            return {"name": "get_clipboard", "arguments": {}}
        elif text_lower == "list processes" or text_lower == "show processes":
            return {"name": "list_processes", "arguments": {"limit": 15}}
        elif text_lower == "list windows" or text_lower == "show windows":
            return {"name": "list_windows", "arguments": {}}

        return None

    async def execute_task(
        self,
        user_prompt: str,
        session_id: str,
        user_confirmed: bool = False,
        on_step_event: Optional[Callable[[str, Dict[str, Any]], Any]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Runs the ReAct loop: reasons, invokes tools, logs observations, and streams tokens."""
        # 1. Persist user prompt in conversation memory
        self.memory.add_message(session_id=session_id, role="user", content=user_prompt)

        # 2. Build conversational history with system prompt
        history_msgs = self.memory.get_messages(session_id=session_id, limit=20)
        messages: List[LLMMessage] = [
            LLMMessage(role="system", content=SYSTEM_PROMPT)
        ]

        # Append tool descriptions in system context
        tool_schemas = self.registry.list_tools()
        if tool_schemas:
            tools_summary = "\nAvailable Tools:\n" + "\n".join(
                f"- {t['name']}: {t['description']} (parameters: {json.dumps(t['parameters'])})"
                for t in tool_schemas
            )
            messages[0].content += tools_summary

        for m in history_msgs:
            messages.append(LLMMessage(role=m["role"], content=m["content"]))

        # 3. Check for immediate direct automation intent
        immediate_tool = self._extract_tool_call(user_prompt)
        if immediate_tool:
            tool_name = immediate_tool.get("name", "")
            tool_args = immediate_tool.get("arguments", {})

            yield {"type": "tool_start", "tool_name": tool_name, "arguments": tool_args}
            if on_step_event:
                await on_step_event("tool_start", {"tool_name": tool_name, "arguments": tool_args})

            tool_res = await self.registry.execute_tool(
                tool_name=tool_name,
                arguments=tool_args,
                user_confirmed=user_confirmed,
            )

            # Log tool execution to memory
            self.memory.log_tool_execution(
                session_id=session_id,
                tool_name=tool_name,
                arguments=tool_args,
                result=tool_res.to_dict(),
                status="success" if tool_res.success else "error",
                execution_time_ms=tool_res.execution_time_ms,
            )

            yield {"type": "tool_result", "tool_name": tool_name, "result": tool_res.to_dict()}

            # Add tool observation to context for model synthesis
            observation_msg = f"Tool '{tool_name}' executed. Result: {json.dumps(tool_res.to_dict())}"
            messages.append(LLMMessage(role="tool", content=observation_msg, name=tool_name))
            messages.append(LLMMessage(
                role="user",
                content=f"Synthesize the result of executing {tool_name} naturally for the user.",
            ))

        # 4. Stream response from AI Runtime
        assistant_content_chunks = []
        yield {"type": "stream_start"}

        async for chunk in self.router.stream_chat(messages=messages):
            if chunk.delta:
                assistant_content_chunks.append(chunk.delta)
                yield {
                    "type": "token",
                    "delta": chunk.delta,
                    "provider": chunk.provider,
                    "model": chunk.model,
                }

        final_content = "".join(assistant_content_chunks)
        # 5. Persist assistant response
        self.memory.add_message(
            session_id=session_id,
            role="assistant",
            content=final_content,
        )

        yield {"type": "stream_end", "full_content": final_content}


# Global agent planner instance
agent_planner = AgentPlanner()
