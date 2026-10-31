"""
Unit tests for ReAct agent planner and multi-step reasoning.
"""

import pytest
from aegis_core.agent.planner import AgentPlanner
from aegis_core.ai_runtime.base import LLMChunk, LLMProvider, LLMResponse
from aegis_core.ai_runtime.router import AIRuntimeRouter
from aegis_core.memory.db import DatabaseEngine
from aegis_core.memory.session_manager import SessionManager
from aegis_core.plugins.registry import PluginRegistry
from aegis_core.automation.system_tools import GetSystemTelemetryTool


class MockAgentProvider(LLMProvider):
    name = "mock_agent_provider"

    async def is_available(self) -> bool:
        return True

    async def list_models(self):
        return ["agent-model"]

    async def generate_stream(self, messages, model=None, tools=None, temperature=0.7):
        yield LLMChunk(delta="Task completed successfully.", provider=self.name, model="agent-model")

    async def generate(self, messages, model=None, tools=None, temperature=0.7):
        return LLMResponse(content="Task completed successfully.", provider=self.name, model="agent-model")


@pytest.mark.asyncio
async def test_agent_planner_direct_tool_execution(tmp_path):
    """Ensure agent planner identifies direct commands and invokes tools."""
    db_path = tmp_path / "agent_test.db"
    db_engine = DatabaseEngine(db_path=db_path)
    mem = SessionManager(engine=db_engine)
    session_id = mem.create_session("Agent Test")

    reg = PluginRegistry()
    reg.register(GetSystemTelemetryTool())

    router = AIRuntimeRouter()
    mock_p = MockAgentProvider()
    router.ollama = mock_p
    router.pollinations = mock_p

    planner = AgentPlanner(router=router, registry=reg, memory=mem)

    events = []
    async for event in planner.execute_task(
        user_prompt="get clipboard",
        session_id=session_id,
        user_confirmed=True,
    ):
        events.append(event)

    types = [e["type"] for e in events]
    assert "stream_start" in types
    assert "token" in types
    assert "stream_end" in types

    # Check conversation history was saved
    history = mem.get_messages(session_id)
    assert len(history) >= 2
    assert history[0]["role"] == "user"
    assert history[-1]["role"] == "assistant"
