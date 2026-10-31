"""
Aegis AI - Natural Language Intent Router & Fast Classifier.
Classifies user speech or typed queries into actionable desktop commands or conversational LLM reasoning
with zero latency, zero cloud APIs, and fuzzy entity extraction.
"""

from enum import Enum
import re
from typing import Any, Dict, Optional


class UserIntent(str, Enum):
    APP_LAUNCH = "app_launch"
    APP_CLOSE = "app_close"
    WINDOW_ACTION = "window_action"
    SYSTEM_QUERY = "system_query"
    CLIPBOARD = "clipboard"
    VOLUME = "volume"
    BRIGHTNESS = "brightness"
    SCREEN_CAPTURE = "screen_capture"
    NOTES = "notes"
    CONVERSATION = "conversation"


class IntentRouter:
    """Fast, zero-latency natural language intent classifier."""

    # Regex patterns for high-frequency Windows desktop operations
    APP_LAUNCH_PATTERNS = [
        (
            r"^(?:please\s+)?(?:can\s+you\s+)?(?:please\s+)?"
            r"(?:open|launch|start|run|fire\s+up)\s+(?:the\s+)?(?P<app>.+?)(?:\s+please)?$"
        ),
        r"^(?:start\s+up|open\s+up)\s+(?P<app>.+?)(?:\s+please)?$",
    ]

    APP_CLOSE_PATTERNS = [
        (
            r"^(?:please\s+)?(?:can\s+you\s+)?(?:please\s+)?"
            r"(?:close|kill|quit|terminate|exit)\s+(?:the\s+)?(?P<app>.+?)(?:\s+please)?$"
        ),
        r"^(?:force\s+close|shut\s+down)\s+(?P<app>.+?)(?:\s+please)?$",
    ]

    WINDOW_MINIMIZE_ALL_PATTERNS = [
        (
            r"^(?:please\s+)?"
            r"(?:minimize\s+all(?:\s+windows)?|show\s+desktop|hide\s+all\s+windows|clear\s+screen)"
            r"(?:\s+please)?$"
        ),
    ]

    WINDOW_SNAP_PATTERNS = [
        (
            r"^(?:please\s+)?"
            r"(?:snap|tile|dock|move)(?:\s+window)?\s+(?:to\s+the\s+)?(?P<side>left|right)"
            r"(?:\s+please)?$"
        ),
        r"^(?:please\s+)?(?:maximize\s+window|maximize|unmaximize|restore\s+window)(?:\s+please)?$",
    ]

    WINDOW_FOCUS_PATTERNS = [
        (
            r"^(?:please\s+)?(?:bring|focus|switch\s+to)\s+(?:the\s+)?"
            r"(?P<app>.+?)(?:\s+to\s+front|\s+window)?(?:\s+please)?$"
        ),
    ]

    SYSTEM_QUERY_PATTERNS = [
        (
            r"^(?:what\s+is\s+my|show|get|check)?\s*"
            r"(?:system\s+telemetry|system\s+info|system\s+status|"
            r"cpu\s+usage|memory\s+usage|ram\s+usage|battery|specs)$"
        ),
    ]

    CLIPBOARD_PATTERNS = [
        r"^(?:what(?:'s|\s+is)\s+on\s+my\s+clipboard|get\s+clipboard|read\s+clipboard|show\s+clipboard)$",
    ]

    SCREEN_CAPTURE_PATTERNS = [
        (
            r"^(?:please\s+)?"
            r"(?:take\s+a\s+screenshot|capture\s+screen|take\s+screenshot|screenshot|capture\s+desktop)"
            r"(?:\s+please)?$"
        ),
    ]

    @classmethod
    def classify_and_route(cls, text: str) -> Optional[Dict[str, Any]]:
        """
        Classifies input text and returns a tool call dictionary if an actionable
        local intent is detected, or None for general conversation.
        """
        raw = text.strip()
        low = raw.lower()

        # 1. Volume Controls
        if re.match(r"^(?:please\s+)?(?:mute|mute\s+audio|mute\s+sound|silence)(?:\s+please)?$", low):
            return {"intent": UserIntent.VOLUME, "name": "control_volume", "arguments": {"action": "mute"}}

        if re.match(r"^(?:please\s+)?(?:unmute|unmute\s+audio|unmute\s+sound)(?:\s+please)?$", low):
            return {"intent": UserIntent.VOLUME, "name": "control_volume", "arguments": {"action": "unmute"}}

        m_vol_set = re.match(r"^(?:please\s+)?(?:set\s+)?volume\s+(?:to\s+)?(?P<lvl>\d+)\%?(?:\s+please)?$", low)
        if m_vol_set:
            lvl = int(m_vol_set.group("lvl"))
            return {
                "intent": UserIntent.VOLUME,
                "name": "control_volume",
                "arguments": {"action": "set", "level": lvl},
            }

        if re.match(
            r"^(?:please\s+)?(?:turn\s+)?(?:volume\s+up|increase\s+volume|louder|raise\s+volume)(?:\s+please)?$",
            low,
        ):
            return {
                "intent": UserIntent.VOLUME,
                "name": "control_volume",
                "arguments": {"action": "increase", "level": 10},
            }

        if re.match(
            r"^(?:please\s+)?(?:turn\s+)?(?:volume\s+down|decrease\s+volume|quieter|lower\s+volume)(?:\s+please)?$",
            low,
        ):
            return {
                "intent": UserIntent.VOLUME,
                "name": "control_volume",
                "arguments": {"action": "decrease", "level": 10},
            }

        # 2. Brightness Controls
        m_br_set = re.match(r"^(?:please\s+)?(?:set\s+)?brightness\s+(?:to\s+)?(?P<lvl>\d+)\%?(?:\s+please)?$", low)
        if m_br_set:
            lvl = int(m_br_set.group("lvl"))
            return {
                "intent": UserIntent.BRIGHTNESS,
                "name": "control_brightness",
                "arguments": {"action": "set", "level": lvl},
            }

        if re.match(
            r"^(?:please\s+)?(?:increase\s+brightness|brighter|raise\s+brightness|brightness\s+up)(?:\s+please)?$",
            low,
        ):
            return {
                "intent": UserIntent.BRIGHTNESS,
                "name": "control_brightness",
                "arguments": {"action": "increase", "level": 10},
            }

        if re.match(
            r"^(?:please\s+)?(?:decrease\s+brightness|lower\s+brightness|"
            r"dim\s+screen|brightness\s+down)(?:\s+please)?$",
            low,
        ):
            return {
                "intent": UserIntent.BRIGHTNESS,
                "name": "control_brightness",
                "arguments": {"action": "decrease", "level": 10},
            }

        # 3. Screen Capture
        for pat in cls.SCREEN_CAPTURE_PATTERNS:
            if re.match(pat, low):
                return {
                    "intent": UserIntent.SCREEN_CAPTURE,
                    "name": "capture_screen",
                    "arguments": {"target": "full"},
                }

        # 4. Quick Notes
        m_note_append = re.match(
            r"^(?:please\s+)?(?:note\s+down(?:\:)?|add\s+note(?:\:)?|"
            r"take\s+a\s+note(?:\:)?|remember\s+that(?:\:)?)\s+(?P<text>.+)$",
            raw,
            re.IGNORECASE,
        )
        if m_note_append:
            note_text = m_note_append.group("text").strip()
            return {
                "intent": UserIntent.NOTES,
                "name": "manage_notes",
                "arguments": {"action": "append", "text": note_text},
            }

        if re.match(
            r"^(?:please\s+)?(?:read|show|get|view)\s+(?:my\s+)?(?:notes|today's\s+notes)(?:\s+please)?$",
            low,
        ):
            return {
                "intent": UserIntent.NOTES,
                "name": "manage_notes",
                "arguments": {"action": "read_today"},
            }

        m_note_search = re.match(
            r"^(?:please\s+)?(?:search\s+notes\s+for|find\s+in\s+notes)\s+(?P<query>.+)$",
            raw,
            re.IGNORECASE,
        )
        if m_note_search:
            q = m_note_search.group("query").strip()
            return {
                "intent": UserIntent.NOTES,
                "name": "manage_notes",
                "arguments": {"action": "search", "query": q},
            }

        # 5. Window Minimize All / Show Desktop
        for pat in cls.WINDOW_MINIMIZE_ALL_PATTERNS:
            if re.match(pat, low):
                return {
                    "intent": UserIntent.WINDOW_ACTION,
                    "name": "minimize_all_windows",
                    "arguments": {},
                }

        # 6. Window Snapping (left, right, maximize)
        for pat in cls.WINDOW_SNAP_PATTERNS:
            m = re.match(pat, low)
            if m:
                side = m.groupdict().get("side") or ("maximize" if "maximize" in low else "restore")
                return {
                    "intent": UserIntent.WINDOW_ACTION,
                    "name": "snap_window",
                    "arguments": {"side": side},
                }

        # 7. Window Focus / Bring to Front
        for pat in cls.WINDOW_FOCUS_PATTERNS:
            m = re.match(pat, low)
            if m:
                app = m.group("app").strip()
                if app not in ["it", "this", "that"]:
                    return {
                        "intent": UserIntent.WINDOW_ACTION,
                        "name": "focus_window_by_title",
                        "arguments": {"title_query": app},
                    }

        # 8. App Launching
        for pat in cls.APP_LAUNCH_PATTERNS:
            m = re.match(pat, low)
            if m:
                app = m.group("app").strip()
                if "clipboard" in app:
                    return {
                        "intent": UserIntent.CLIPBOARD,
                        "name": "get_clipboard",
                        "arguments": {},
                    }
                if any(k in app for k in ["system", "telemetry", "specs", "cpu"]):
                    return {
                        "intent": UserIntent.SYSTEM_QUERY,
                        "name": "get_system_telemetry",
                        "arguments": {},
                    }
                return {
                    "intent": UserIntent.APP_LAUNCH,
                    "name": "launch_application",
                    "arguments": {"app_name": app},
                }

        # 9. App Closing
        for pat in cls.APP_CLOSE_PATTERNS:
            m = re.match(pat, low)
            if m:
                app = m.group("app").strip()
                return {
                    "intent": UserIntent.APP_CLOSE,
                    "name": "close_application",
                    "arguments": {"process_name": app},
                }

        # 10. System Queries
        for pat in cls.SYSTEM_QUERY_PATTERNS:
            if re.match(pat, low):
                return {
                    "intent": UserIntent.SYSTEM_QUERY,
                    "name": "get_system_telemetry",
                    "arguments": {},
                }

        # 11. Clipboard Queries
        for pat in cls.CLIPBOARD_PATTERNS:
            if re.match(pat, low):
                return {
                    "intent": UserIntent.CLIPBOARD,
                    "name": "get_clipboard",
                    "arguments": {},
                }

        # Default: Conversation / ReAct LLM Reasoning
        return None
