"""
Unit and integration tests for Aegis AI Vision AI & Ask My Screen engine.
"""

from unittest.mock import patch
from fastapi.testclient import TestClient
from aegis_core.main import app
from aegis_core.ai_runtime.vision_analyzer import (
    ScreenVisionAnalyzer,
    screen_vision_analyzer,
)
from aegis_core.automation.intent_router import IntentRouter, UserIntent
from aegis_core.automation.system_tools import AnalyzeScreenTool

client = TestClient(app)


def test_vision_intent_routing_arabic():
    """Verifies that Arabic Vision AI queries correctly route to analyze_screen tool."""
    prompts = [
        "حلل الشاشة",
        "ماذا ترى على الشاشة",
        "حلل ما يظهر على الشاشة",
        "اقرأ الشاشة واشرح المحتوى",
        "تحليل الشاشة الذكي",
    ]
    for p in prompts:
        routed = IntentRouter.classify_and_route(p)
        assert routed is not None, f"Failed to route: {p}"
        assert routed["intent"] == UserIntent.VISION_ANALYSIS
        assert routed["name"] == "analyze_screen"


def test_vision_intent_routing_english():
    """Verifies that English Vision AI queries route to analyze_screen tool."""
    prompts = [
        "ask my screen",
        "analyze screen please",
        "what is on my screen",
        "explain screen",
    ]
    for p in prompts:
        routed = IntentRouter.classify_and_route(p)
        assert routed is not None, f"Failed to route: {p}"
        assert routed["intent"] == UserIntent.VISION_ANALYSIS
        assert routed["name"] == "analyze_screen"


def test_inspect_desktop_context():
    """Verifies desktop context extraction returns foreground and open windows."""
    analyzer = ScreenVisionAnalyzer()
    ctx = analyzer.inspect_desktop_context()
    assert isinstance(ctx, dict)
    assert "foreground_window" in ctx
    assert "open_windows" in ctx
    assert "open_windows_count" in ctx


@patch("aegis_core.automation.screen_capture.ScreenCaptureEngine.capture")
async def test_analyze_screen_flow(mock_capture):
    """Verifies end-to-end screen analysis execution."""
    mock_capture.return_value = {
        "success": True,
        "path": "storage/cache/screenshots/test.jpg",
        "base64": "fake_base64",
        "width": 1920,
        "height": 1080,
        "latency_ms": 45.0,
    }

    analyzer = ScreenVisionAnalyzer()
    res = await analyzer.analyze_screen(query="ماذا يوجد على الشاشة", target="full", language="ar")
    assert res["success"] is True
    assert "analysis" in res
    assert "resolution" in res
    assert res["resolution"] == "1920x1080"


@patch.object(screen_vision_analyzer, "analyze_screen")
def test_analyze_screen_tool(mock_analyze):
    """Verifies AnalyzeScreenTool execution."""
    import asyncio

    mock_analyze.return_value = {
        "success": True,
        "analysis": "تم فحص الشاشة بنجاح.",
        "active_window": "Visual Studio Code",
        "resolution": "1920x1080",
        "screenshot_path": "test.jpg",
        "screenshot_url": "/api/vision/latest-screen",
        "latency_ms": 50.0,
        "vision_model_used": "Aegis Vision Synthesizer",
        "has_local_vision_model": False,
        "open_windows": ["VS Code", "Chrome"],
    }

    tool = AnalyzeScreenTool()
    tool_res = asyncio.run(tool.execute(query="حلل الشاشة"))
    assert tool_res.success is True
    assert "تم فحص الشاشة" in tool_res.message
    assert tool_res.data["active_window"] == "Visual Studio Code"


def test_api_vision_analyze():
    """Verifies POST /api/vision/analyze API endpoint."""
    mock_res = {
        "success": True,
        "query": "حلل الشاشة",
        "analysis": "شاشة التطوير نشطة.",
        "active_window": "Chrome",
        "open_windows": ["Chrome"],
        "resolution": "1920x1080",
        "screenshot_path": "path.jpg",
        "screenshot_url": "/api/vision/latest-screen",
        "latency_ms": 60.0,
        "vision_model_used": "Test Vision Model",
        "has_local_vision_model": True,
    }
    with patch("aegis_core.ai_runtime.vision_analyzer.screen_vision_analyzer.analyze_screen", return_value=mock_res):
        response = client.post("/api/vision/analyze", json={"query": "حلل الشاشة", "target": "full"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["active_window"] == "Chrome"


def test_arbitrary_screen_questions_routing():
    """Verifies that arbitrary and custom natural screen questions route to analyze_screen tool."""
    prompts = [
        "شو في بالشاشة",
        "شو مكتوب بالشاشة",
        "ما هذا الخطأ بالشاشة",
        "اقرأ المكتوب بالشاشة",
        "اشرح الكود المعروض على الشاشة",
        "ترجم النص الظاهر على الشاشة",
        "what is this error on my screen",
        "read the text on my screen",
    ]
    for p in prompts:
        routed = IntentRouter.classify_and_route(p)
        assert routed is not None, f"Failed to route arbitrary screen question: {p}"
        assert routed["intent"] == UserIntent.VISION_ANALYSIS
        assert routed["name"] == "analyze_screen"

