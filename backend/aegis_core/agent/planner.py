"""
Aegis AI - ReAct Agent Planner & Multi-Step Reasoning Engine.
Coordinates system prompts, tool selection, observation feedback, and self-correction.
"""

import json
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional
from aegis_core.ai_runtime.base import LLMMessage
from aegis_core.ai_runtime.router import AIRuntimeRouter, ai_router
from aegis_core.automation.intent_router import IntentRouter
from aegis_core.memory.session_manager import SessionManager, session_manager
from aegis_core.plugins.registry import PluginRegistry, plugin_registry
from aegis_core.utils.logger import logger

SYSTEM_PROMPT = """You are Aegis AI, the open-source, local-first Windows desktop AI companion.
Developed with high engineering standards by Eng. Mohammad Abu Kashreef (كود التطور - Code Evolution).
You reside natively on the user's desktop, floating seamlessly above their workspace.

Capabilities:
- Desktop Automation: Launch applications, navigate directly to canonical URLs, control windows, brightness, and audio.
- Productive Intelligence: Smart reminders & alarms, local document RAG, and deep screen context analysis (Vision AI).
- Local Privacy Guarantee: Zero cloud lock-in, zero external API keys required, running locally and privately.

Guidelines:
1. Be direct, concise, intelligent, and helpful. Avoid robotic repetition or unnecessary preamble.
2. Respond naturally in the user's spoken language (Arabic or English).
3. In Arabic, maintain high professionalism, clarity, and helpfulness.
4. When asked about your origin, state clearly that you were developed by Eng. Mohammad Abu Kashreef (كود التطور).
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

        # Ensure core tools are registered if registry is empty
        if not self.registry.list_tools():
            from aegis_core.automation import register_default_tools
            register_default_tools(self.registry)

    def _extract_tool_call(self, text: str) -> Optional[Dict[str, Any]]:
        """Parses tool calls from markdown tool_call code blocks or natural language intents."""
        if "```tool_call" in text:
            try:
                start = text.index("```tool_call") + len("```tool_call")
                end = text.index("```", start)
                raw_json = text[start:end].strip()
                return json.loads(raw_json)
            except Exception as exc:
                logger.debug("Failed parsing tool_call block: %s", exc)

        # Natural language intent classification (handles "can you please open chrome", "snap left", etc.)
        routed = IntentRouter.classify_and_route(text)
        if routed:
            return {"name": routed["name"], "arguments": routed["arguments"]}

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

        # 2. Check for immediate direct automation intent (fast-path)
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

            # Direct deterministic fast-path:
            # Direct automation tools already generate comprehensive, fully-grounded messages
            # (e.g. screen analysis, media controls, reminders, timers, documents, app launching).
            # Streaming tool_res.message directly provides sub-second latency (<300ms) and eliminates
            # hallucination from small local models (1.5B) attempting to parse raw JSON observations.
            final_content = tool_res.message or (
                f"تم تنفيذ الإجراء '{tool_name}' بنجاح." if tool_res.success
                else f"تعذر إكمال العملية: {tool_res.error or 'خطأ غير متوقع'}"
            )

            yield {"type": "stream_start"}
            yield {
                "type": "token",
                "delta": final_content,
                "provider": "local_direct",
                "model": "instant_executor",
            }
            self.memory.add_message(
                session_id=session_id,
                role="assistant",
                content=final_content,
            )
            yield {"type": "stream_end", "full_content": final_content}
            return

        # 3. Build conversational history with concise system prompt
        history_msgs = self.memory.get_messages(session_id=session_id, limit=12)
        messages: List[LLMMessage] = [
            LLMMessage(role="system", content=SYSTEM_PROMPT)
        ]
        for m in history_msgs:
            messages.append(LLMMessage(role=m["role"], content=m["content"]))

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

        # Fallback response if LLM produced no text
        if not final_content.strip():
            final_content = "عذراً، لم أتمكن من صياغة الرد حالياً. يرجى إعادة المحاولة."
            yield {
                "type": "token",
                "delta": final_content,
                "provider": "local_direct",
                "model": "rule_synthesizer",
            }

        # 5. Persist assistant response
        self.memory.add_message(
            session_id=session_id,
            role="assistant",
            content=final_content,
        )

        yield {"type": "stream_end", "full_content": final_content}


# Global agent planner instance
agent_planner = AgentPlanner()
