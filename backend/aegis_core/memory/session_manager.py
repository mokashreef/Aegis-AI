"""
Aegis AI - Session & Conversational Memory Manager.
"""

import json
import uuid
from typing import Any, Dict, List, Optional
from aegis_core.memory.db import DatabaseEngine, db_engine
from aegis_core.utils.logger import logger


class SessionManager:
    """Handles session creation, conversation history retrieval, and tool execution logging."""

    def __init__(self, engine: Optional[DatabaseEngine] = None):
        self.engine = engine or db_engine

    def create_session(self, title: str = "New Conversation", metadata: Optional[Dict[str, Any]] = None) -> str:
        """Generates a new session ID and persists it."""
        session_id = str(uuid.uuid4())
        meta_json = json.dumps(metadata or {})
        with self.engine.get_connection() as conn:
            conn.execute(
                "INSERT INTO sessions (id, title, metadata) VALUES (?, ?, ?);",
                (session_id, title, meta_json),
            )
        logger.debug("Created session %s with title '%s'", session_id, title)
        return session_id

    def list_sessions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieves recent sessions ordered by latest update."""
        with self.engine.get_connection() as conn:
            cursor = conn.execute(
                "SELECT id, title, created_at, updated_at, metadata FROM sessions ORDER BY updated_at DESC LIMIT ?;",
                (limit,),
            )
            rows = cursor.fetchall()
            return [
                {
                    "id": row["id"],
                    "title": row["title"],
                    "created_at": str(row["created_at"]),
                    "updated_at": str(row["updated_at"]),
                    "metadata": json.loads(row["metadata"] or "{}"),
                }
                for row in rows
            ]

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        model: Optional[str] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
    ) -> int:
        """Appends a message to the session's conversational history."""
        tool_calls_json = json.dumps(tool_calls) if tool_calls else None
        with self.engine.get_connection() as conn:
            # Ensure session exists or create on the fly
            conn.execute(
                """
                INSERT INTO sessions (id, title)
                VALUES (?, 'Conversation')
                ON CONFLICT(id) DO UPDATE SET updated_at = CURRENT_TIMESTAMP;
                """,
                (session_id,),
            )

            cursor = conn.execute(
                """
                INSERT INTO messages (session_id, role, content, model, tool_calls)
                VALUES (?, ?, ?, ?, ?);
                """,
                (session_id, role, content, model, tool_calls_json),
            )
            msg_id = cursor.lastrowid or 0
        return msg_id

    def get_messages(self, session_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Retrieves messages for a session formatted for LLM context injection."""
        with self.engine.get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, role, content, model, tool_calls, created_at
                FROM messages
                WHERE session_id = ?
                ORDER BY id ASC
                LIMIT ?;
                """,
                (session_id, limit),
            )
            rows = cursor.fetchall()
            messages = []
            for row in rows:
                msg = {
                    "id": row["id"],
                    "role": row["role"],
                    "content": row["content"],
                    "model": row["model"],
                    "created_at": str(row["created_at"]),
                }
                if row["tool_calls"]:
                    msg["tool_calls"] = json.loads(row["tool_calls"])
                messages.append(msg)
            return messages

    def log_tool_execution(
        self,
        session_id: Optional[str],
        tool_name: str,
        arguments: Dict[str, Any],
        result: Any,
        status: str,
        execution_time_ms: float = 0.0,
    ) -> int:
        """Records a tool execution invocation in the audit log."""
        with self.engine.get_connection() as conn:
            cursor = conn.execute(
                """
                INSERT INTO tool_executions (session_id, tool_name, arguments, result, status, execution_time_ms)
                VALUES (?, ?, ?, ?, ?, ?);
                """,
                (
                    session_id,
                    tool_name,
                    json.dumps(arguments),
                    json.dumps(result) if not isinstance(result, str) else result,
                    status,
                    execution_time_ms,
                ),
            )
            return cursor.lastrowid or 0

    def set_preference(self, key: str, value: Any) -> None:
        """Stores a persistent user preference."""
        val_str = json.dumps(value) if not isinstance(value, str) else value
        with self.engine.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO user_preferences (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP;
                """,
                (key, val_str),
            )

    def get_preference(self, key: str, default: Any = None) -> Any:
        """Retrieves a persistent user preference."""
        with self.engine.get_connection() as conn:
            cursor = conn.execute("SELECT value FROM user_preferences WHERE key = ?;", (key,))
            row = cursor.fetchone()
            if not row:
                return default
            val = row["value"]
            try:
                return json.loads(val)
            except Exception:
                return val

    def get_all_preferences(self) -> Dict[str, Any]:
        """Retrieves all user preferences merged with sensible default values."""
        prefs = dict(DEFAULT_USER_PREFERENCES)
        with self.engine.get_connection() as conn:
            cursor = conn.execute("SELECT key, value FROM user_preferences;")
            for row in cursor.fetchall():
                k = row["key"]
                v = row["value"]
                try:
                    prefs[k] = json.loads(v)
                except Exception:
                    prefs[k] = v
        return prefs

    def update_preferences(self, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Bulk updates user preferences and returns the updated state."""
        for key, value in updates.items():
            self.set_preference(key, value)
        return self.get_all_preferences()


DEFAULT_USER_PREFERENCES: Dict[str, Any] = {
    "theme": "dark",
    "language": "auto",
    "auto_speak": False,
    "tts_voice": "ar-SA-HamedNeural",
    "tts_rate": "+0%",
    "default_browser": "chrome",
    "start_with_windows": False,
    "quick_actions": [
        {
            "id": "yt",
            "title": "YouTube in Chrome",
            "title_ar": "يوتيوب في كروم",
            "command": "افتح موقع يوتيوب بمتصفح كروم",
            "icon": "globe",
            "enabled": True,
        },
        {
            "id": "google",
            "title": "Google in Comet",
            "title_ar": "جوجل في كومت",
            "command": "افتح جوجل بمتصفح كومت",
            "icon": "globe",
            "enabled": True,
        },
        {
            "id": "notepad",
            "title": "Launch Notepad",
            "title_ar": "فتح المفكرة",
            "command": "افتح المفكرة",
            "icon": "app",
            "enabled": True,
        },
        {
            "id": "screenshot",
            "title": "Take Screenshot",
            "title_ar": "أخذ لقطة شاشة",
            "command": "صور الشاشة",
            "icon": "camera",
            "enabled": True,
        },
        {
            "id": "minimize",
            "title": "Show Desktop",
            "title_ar": "إظهار سطح المكتب",
            "command": "صغر كل النوافذ",
            "icon": "layers",
            "enabled": True,
        },
    ],
}

# Global session manager instance
session_manager = SessionManager()

