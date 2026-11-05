import pytest
"""
Tests for Canonical Website Resolution, Arbitrary Screen Vision Queries,
and Silent Background Execution.
"""

import subprocess
from aegis_core.automation.intent_router import (
    IntentRouter,
    UserIntent,
    resolve_url_name,
    resolve_app_name,
)
from aegis_core.automation.system_tools import LaunchAppTool, OpenUrlTool


def test_canonical_website_resolution_accuracy():
    """Verify that colloquial names route to canonical official URLs without search engine redirects."""
    cases = [
        ("كود التطور", "https://code-elta6ur.net"),
        ("كود التطور دوت نت", "https://code-elta6ur.net"),
        ("موقع كود التطور", "https://code-elta6ur.net"),
        ("كلود", "https://claude.ai"),
        ("claude", "https://claude.ai"),
        ("جيميني", "https://gemini.google.com"),
        ("gemini", "https://gemini.google.com"),
        ("كانفا", "https://www.canva.com"),
        ("فيجما", "https://www.figma.com"),
        ("يوتيوب", "https://www.youtube.com"),
        ("شات جي بي تي", "https://chatgpt.com"),
        ("تويتر", "https://x.com"),
        ("اكس", "https://x.com"),
    ]
    for spoken, expected_url in cases:
        resolved = resolve_url_name(spoken)
        assert resolved == expected_url, f"Failed for '{spoken}': expected '{expected_url}', got '{resolved}'"


def test_spoken_compound_url_navigation():
    """Verify compound commands like 'كروم و افتح موقع كود التطور' route accurately."""
    res = IntentRouter.classify_and_route("افتح المتصفح و افتح كود التطور")
    assert res is not None
    assert res["intent"] == UserIntent.OPEN_URL
    assert res["arguments"]["url"] == "https://code-elta6ur.net"

    res2 = IntentRouter.classify_and_route("افتح موقع كلود بكروم")
    assert res2 is not None
    assert res2["intent"] == UserIntent.OPEN_URL
    assert res2["arguments"]["url"] == "https://claude.ai"


def test_arbitrary_screen_inquiry_routing():
    """Verify that arbitrary questions about the screen route to analyze_screen."""
    queries = [
        "شو هذا الخطأ الموجود بالشاشة؟",
        "اقرأ الكود المعروض على الشاشة",
        "ماذا ترى في الشاشة حالياً؟",
        "ترجم النص الموجود بالشاشة",
        "في الشاشة: ما هو اسم البرنامج المفتوح؟",
        "[Screen Analysis] what is that syntax error in the terminal?",
        "what's on my screen right now?",
    ]
    for q in queries:
        routed = IntentRouter.classify_and_route(q)
        assert routed is not None, f"Failed routing for: {q}"
        assert routed["name"] == "analyze_screen", f"Expected analyze_screen for '{q}', got {routed['name']}"


def test_resolve_app_name_precision():
    """Verify common Arabic app names resolve to correct Windows executables."""
    assert resolve_app_name("المفكرة") == "notepad"
    assert resolve_app_name("الرسام") == "mspaint"
    assert resolve_app_name("الحاسبة") == "calc"
    assert resolve_app_name("كالكوليتر") == "calc"
    assert resolve_app_name("الوورد") == "winword"
    assert resolve_app_name("الاكسل") == "excel"


def test_silent_execution_flags():
    """Verify that CREATE_NO_WINDOW constant is defined and valid on Windows."""
    assert hasattr(subprocess, "CREATE_NO_WINDOW")
    assert subprocess.CREATE_NO_WINDOW == 0x08000000


def test_tools_instantiation():
    """Verify tool wrappers instantiate cleanly."""
    launch_tool = LaunchAppTool()
    open_url_tool = OpenUrlTool()
    assert launch_tool.name == "launch_application"
    assert open_url_tool.name == "open_url"


@pytest.mark.asyncio
async def test_system_diagnostics_endpoint():
    """Verify system diagnostics endpoint returns healthy status and metadata."""
    from aegis_core.main import app
    from httpx import ASGITransport, AsyncClient

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/system/diagnostics")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert "Mohammad Abu Kashreef" in data["author"]
        assert data["zero_api_keys_enforced"] is True
        assert data["silent_mode"] is True
