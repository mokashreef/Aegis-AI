"""
Unit and integration tests for Aegis AI Native Windows Media Playback Controls.
"""

from unittest.mock import patch
from fastapi.testclient import TestClient

from aegis_core.main import app
from aegis_core.automation.intent_router import IntentRouter, UserIntent
from aegis_core.automation.media_manager import MediaManager, media_manager
from aegis_core.automation.system_tools import ControlMediaTool

client = TestClient(app)


def test_media_manager_actions():
    """Verifies MediaManager methods return valid structured dictionaries."""
    with patch.object(MediaManager, "_send_media_key", return_value=True):
        res_play = media_manager.play_pause()
        assert res_play["success"] is True
        assert res_play["action"] == "play_pause"

        res_next = media_manager.next_track()
        assert res_next["success"] is True
        assert res_next["action"] == "next"

        res_prev = media_manager.previous_track()
        assert res_prev["success"] is True
        assert res_prev["action"] == "previous"

        res_stop = media_manager.stop()
        assert res_stop["success"] is True
        assert res_stop["action"] == "stop"


def test_media_manager_execute_action():
    """Verifies execute_action dispatches correctly."""
    with patch.object(MediaManager, "_send_media_key", return_value=True):
        assert media_manager.execute_action("play")["action"] == "play_pause"
        assert media_manager.execute_action("pause")["action"] == "play_pause"
        assert media_manager.execute_action("skip")["action"] == "next"
        assert media_manager.execute_action("prev")["action"] == "previous"
        assert media_manager.execute_action("stop")["action"] == "stop"

        # Invalid action returns error
        invalid = media_manager.execute_action("unknown_cmd")
        assert invalid["success"] is False
        assert "error" in invalid


def test_media_intent_routing_arabic():
    """Verifies Arabic spoken/typed media commands route to control_media."""
    cases = [
        ("شغل الموسيقى", "play_pause"),
        ("وقف الموسيقى", "play_pause"),
        ("المقطع التالي", "next"),
        ("الأغنية التالية", "next"),
        ("المقطع السابق", "previous"),
        ("الأغنية السابقة", "previous"),
        ("إيقاف الموسيقى", "stop"),
        ("ايقاف المقطع", "stop"),
    ]
    for prompt, expected_action in cases:
        routed = IntentRouter.classify_and_route(prompt)
        assert routed is not None, f"Failed to route '{prompt}'"
        assert routed["name"] == "control_media"
        assert routed["intent"] == UserIntent.MEDIA
        assert routed["arguments"]["action"] == expected_action


def test_media_intent_routing_english():
    """Verifies English media commands route to control_media."""
    cases = [
        ("play music", "play_pause"),
        ("pause music", "play_pause"),
        ("next track", "next"),
        ("skip track", "next"),
        ("previous track", "previous"),
        ("prev track", "previous"),
        ("stop music", "stop"),
        ("stop media", "stop"),
    ]
    for prompt, expected_action in cases:
        routed = IntentRouter.classify_and_route(prompt)
        assert routed is not None, f"Failed to route '{prompt}'"
        assert routed["name"] == "control_media"
        assert routed["intent"] == UserIntent.MEDIA
        assert routed["arguments"]["action"] == expected_action


@patch.object(MediaManager, "_send_media_key", return_value=True)
async def test_control_media_tool_execution(mock_send):
    """Verifies ControlMediaTool executes and returns ToolResult."""
    tool = ControlMediaTool()

    res_pp = await tool.execute(action="play_pause")
    assert res_pp.success is True
    assert "play_pause" in res_pp.data["action"]

    res_next = await tool.execute(action="next")
    assert res_next.success is True
    assert "next" in res_next.data["action"]


def test_api_media_endpoints():
    """Verifies REST endpoints for media playback control."""
    with patch.object(MediaManager, "_send_media_key", return_value=True):
        # 1. POST /api/media/control
        res1 = client.post("/api/media/control", json={"action": "play_pause"})
        assert res1.status_code == 200
        assert res1.json()["action"] == "play_pause"

        # 2. POST /api/media/play-pause
        res2 = client.post("/api/media/play-pause")
        assert res2.status_code == 200
        assert res2.json()["success"] is True

        # 3. POST /api/media/next
        res3 = client.post("/api/media/next")
        assert res3.status_code == 200
        assert res3.json()["action"] == "next"

        # 4. POST /api/media/previous
        res4 = client.post("/api/media/previous")
        assert res4.status_code == 200
        assert res4.json()["action"] == "previous"

        # 5. POST /api/media/stop
        res5 = client.post("/api/media/stop")
        assert res5.status_code == 200
        assert res5.json()["action"] == "stop"
