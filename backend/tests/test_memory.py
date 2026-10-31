"""
Unit tests for SQLite database engine and session manager.
"""

import tempfile
from pathlib import Path
from aegis_core.memory.db import DatabaseEngine
from aegis_core.memory.session_manager import SessionManager


def test_database_init_and_session_lifecycle():
    """Tests session creation, message persistence, and preference storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_db_path = Path(tmpdir) / "test_aegis.db"
        engine = DatabaseEngine(db_path=test_db_path)
        mgr = SessionManager(engine=engine)

        # 1. Create Session
        session_id = mgr.create_session(title="Unit Test Conversation", metadata={"author": "tester"})
        assert session_id is not None

        # 2. Add Messages
        msg1_id = mgr.add_message(session_id=session_id, role="user", content="Hello Aegis")
        msg2_id = mgr.add_message(session_id=session_id, role="assistant", content="Hello! How can I help?")
        assert msg1_id > 0
        assert msg2_id > msg1_id

        # 3. Retrieve Messages
        msgs = mgr.get_messages(session_id=session_id)
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user"
        assert msgs[0]["content"] == "Hello Aegis"
        assert msgs[1]["role"] == "assistant"

        # 4. Tool Execution Logging
        exec_id = mgr.log_tool_execution(
            session_id=session_id,
            tool_name="launch_application",
            arguments={"app_name": "calc.exe"},
            result={"status": "success"},
            status="success",
            execution_time_ms=12.5,
        )
        assert exec_id > 0

        # 5. User Preferences
        mgr.set_preference("theme", "glassmorphic_dark")
        pref = mgr.get_preference("theme")
        assert pref == "glassmorphic_dark"

