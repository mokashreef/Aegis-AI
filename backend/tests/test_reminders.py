"""
Unit and integration tests for Aegis AI Smart Reminders, Timers & Windows Alerts Engine.
"""

from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient

from aegis_core.main import app
from aegis_core.automation.intent_router import IntentRouter, UserIntent
from aegis_core.automation.reminder_manager import ReminderManager
from aegis_core.automation.system_tools import (
    CancelReminderTool,
    ListRemindersTool,
    SetReminderTool,
    SetTimerTool,
)

client = TestClient(app)


def test_relative_duration_parsing():
    """Verifies colloquial Arabic and English relative durations are correctly converted to seconds."""
    cases = [
        ("مؤقت 10 دقائق", 600),
        ("اضبط مؤقت 5 دقائق", 300),
        ("مؤقت دقيقة ونصف", 90),
        ("ذكرني بعد نص ساعة", 1800),
        ("نبهني بعد ربع ساعة", 900),
        ("ساعة ونص", 5400),
        ("timer for 15 minutes", 900),
        ("set timer 30 seconds", 30),
        ("half an hour", 1800),
    ]
    for text, expected_sec in cases:
        sec, _ = ReminderManager.parse_relative_duration(text)
        assert sec == expected_sec, f"Failed for '{text}': got {sec}, expected {expected_sec}"


def test_absolute_time_parsing():
    """Verifies clock time parsing for reminders."""
    now = datetime.now()

    # Afternoon Arabic
    dt1, _ = ReminderManager.parse_absolute_time("ذكرني الساعة 4:30 عصراً باجتماع")
    assert dt1 is not None
    assert dt1.hour == 16
    assert dt1.minute == 30

    # Morning Arabic
    dt2, _ = ReminderManager.parse_absolute_time("نبهني الساعة 9 صباحاً")
    assert dt2 is not None
    assert dt2.hour == 9
    assert dt2.minute == 0

    # English PM
    dt3, _ = ReminderManager.parse_absolute_time("remind me at 5:15 pm to call client")
    assert dt3 is not None
    assert dt3.hour == 17
    assert dt3.minute == 15

    # Target should be in future
    assert dt1 >= now or (dt1 + timedelta(days=1)) >= now


def test_timer_intent_routing():
    """Verifies that timer commands route to set_timer with duration_seconds."""
    prompts = [
        ("اضبط مؤقت 10 دقائق", "set_timer", UserIntent.TIMER),
        ("مؤقت 5 دقائق", "set_timer", UserIntent.TIMER),
        ("ذكرني بعد نص ساعة", "set_timer", UserIntent.TIMER),
        ("set timer for 15 minutes", "set_timer", UserIntent.TIMER),
        ("timer 45 seconds", "set_timer", UserIntent.TIMER),
    ]
    for prompt, expected_tool, expected_intent in prompts:
        routed = IntentRouter.classify_and_route(prompt)
        assert routed is not None, f"Failed to route '{prompt}'"
        assert routed["name"] == expected_tool
        assert routed["intent"] == expected_intent
        assert routed["arguments"]["duration_seconds"] > 0


def test_reminder_intent_routing():
    """Verifies that scheduled clock reminder commands route to set_reminder."""
    prompts = [
        ("منبه الساعة 7", "set_reminder", UserIntent.REMINDER),
        ("نبهني الساعة 4:30 عصراً", "set_reminder", UserIntent.REMINDER),
        ("ذكرني الساعة 9 صباحاً", "set_reminder", UserIntent.REMINDER),
        ("remind me at 5 pm to call", "set_reminder", UserIntent.REMINDER),
    ]
    for prompt, expected_tool, expected_intent in prompts:
        routed = IntentRouter.classify_and_route(prompt)
        assert routed is not None, f"Failed to route '{prompt}'"
        assert routed["name"] == expected_tool
        assert routed["intent"] == expected_intent


def test_list_and_cancel_intent_routing():
    """Verifies listing and cancelling reminders via intent router."""
    routed_list = IntentRouter.classify_and_route("اعرض المنبهات")
    assert routed_list is not None
    assert routed_list["name"] == "list_reminders"

    routed_list_en = IntentRouter.classify_and_route("list timers")
    assert routed_list_en is not None
    assert routed_list_en["name"] == "list_reminders"

    routed_cancel = IntentRouter.classify_and_route("الغاء المؤقت")
    assert routed_cancel is not None
    assert routed_cancel["name"] == "cancel_reminder"

    routed_cancel_en = IntentRouter.classify_and_route("stop timer")
    assert routed_cancel_en is not None
    assert routed_cancel_en["name"] == "cancel_reminder"


def test_reminder_manager_crud():
    """Tests ReminderManager database operations: create, list, cancel, check due."""
    mgr = ReminderManager()

    # 1. Create a 1-second timer
    timer_item = mgr.create_timer(duration_seconds=1, title="اختبار مؤقت")
    assert timer_item.id.startswith("timer_")
    assert timer_item.status == "active"

    # 2. List reminders
    active_items = mgr.list_reminders(status="active")
    assert any(it.id == timer_item.id for it in active_items)

    # 3. Create absolute reminder
    future_dt = datetime.now() + timedelta(hours=2)
    rem_item = mgr.create_reminder(due_dt=future_dt, title="موعد المستشفى")
    assert rem_item.id.startswith("rem_")

    # 4. Cancel reminder
    ok = mgr.cancel_reminder(rem_item.id)
    assert ok is True
    cancelled_items = mgr.list_reminders(status="cancelled")
    assert any(it.id == rem_item.id for it in cancelled_items)

    # 5. Clean up
    mgr.cancel_reminder(timer_item.id)


@pytest.mark.asyncio
async def test_reminder_tools_execution():
    """Tests execution of SetTimerTool, ListRemindersTool, and CancelReminderTool."""
    set_tool = SetTimerTool()
    res = await set_tool.execute(duration_seconds=120, title="غلي الشاي")
    assert res.success is True
    assert "120" in res.message or "دقيقة" in res.message
    assert res.data["status"] == "active"

    list_tool = ListRemindersTool()
    res_list = await list_tool.execute(status="active")
    assert res_list.success is True
    assert res_list.data["count"] >= 1

    rem_tool = SetReminderTool()
    res_rem = await rem_tool.execute(target_time="10 دقائق", title="مراجعة الكود")
    assert res_rem.success is True

    cancel_tool = CancelReminderTool()
    res_cancel = await cancel_tool.execute(reminder_id=res.data["id"])
    assert res_cancel.success is True
    assert "إلغاء" in res_cancel.message
    await cancel_tool.execute(reminder_id=res_rem.data["id"])


def test_api_reminder_endpoints():
    """Tests REST endpoints for timers and reminders."""
    # 1. Create timer via REST
    res_timer = client.post("/api/reminders/timer", json={"duration_seconds": 60, "title": "استراحة"})
    assert res_timer.status_code == 200
    timer_data = res_timer.json()
    assert timer_data["success"] is True
    timer_id = timer_data["reminder"]["id"]

    # 2. List reminders via REST
    res_list = client.get("/api/reminders")
    assert res_list.status_code == 200
    reminders = res_list.json()
    assert any(r["id"] == timer_id for r in reminders)

    # 3. Cancel latest timer via REST
    res_cancel = client.post("/api/reminders/cancel-latest")
    assert res_cancel.status_code == 200
    assert res_cancel.json()["success"] is True
