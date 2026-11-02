"""
Aegis AI - Smart Reminders, Timers & Windows System Alerts Engine.
Provides persistent, local, zero-cloud timer tracking, scheduled alarms,
and native Windows notification toasts with audio chimes and HUD broadcasts.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
import re
import time
from typing import Any, Dict, List, Optional, Tuple
import uuid

from aegis_core.memory.db import db_engine
from aegis_core.utils.logger import logger


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS reminders (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    due_timestamp REAL NOT NULL,
    due_time_str TEXT NOT NULL,
    duration_seconds INTEGER DEFAULT 0,
    remind_type TEXT NOT NULL CHECK(remind_type IN ('timer', 'reminder', 'alarm')),
    status TEXT NOT NULL CHECK(status IN ('active', 'completed', 'cancelled')),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reminders_status_due ON reminders(status, due_timestamp);
"""


@dataclass
class ReminderItem:
    """Represents a scheduled timer, reminder, or alarm."""

    id: str
    title: str
    due_timestamp: float
    due_time_str: str
    duration_seconds: int
    remind_type: str
    status: str
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        remaining = max(0, int(self.due_timestamp - time.time())) if self.status == "active" else 0
        return {
            "id": self.id,
            "title": self.title,
            "due_timestamp": self.due_timestamp,
            "due_time_str": self.due_time_str,
            "duration_seconds": self.duration_seconds,
            "remind_type": self.remind_type,
            "status": self.status,
            "created_at": self.created_at,
            "remaining_seconds": remaining,
        }


class ReminderManager:
    """Manages timer and alarm persistence, parsing, and Windows alert triggering."""

    def __init__(self, db=None):
        self.db = db or db_engine
        self._init_schema()

    def _init_schema(self) -> None:
        try:
            with self.db.get_connection() as conn:
                conn.executescript(SCHEMA_SQL)
        except Exception as exc:
            logger.error("Failed to initialize reminders schema: %s", exc)

    @classmethod
    def parse_relative_duration(cls, text: str) -> Tuple[int, str]:
        """
        Parses Arabic or English colloquial duration phrases into seconds and title.
        Supports: 'نص ساعة', 'ربع ساعة', 'ساعة ونص', '10 دقائق', '15 mins', etc.
        """
        text_clean = text.strip()
        duration_seconds = 0

        # 1. Compound hour phrases
        if re.search(r"\b(?:ساعة\s*و\s*نصف|ساعة\s*ونص|ساعه\s*ونص|ساعه\s*و\s*نصف)\b", text_clean):
            duration_seconds += 5400
            text_clean = re.sub(r"\b(?:ساعة\s*و\s*نصف|ساعة\s*ونص|ساعه\s*ونص|ساعه\s*و\s*نصف)\b", " ", text_clean)
        elif re.search(r"\b(?:ساعة\s*و\s*ربع|ساعة\s*وربع|ساعه\s*وربع|ساعه\s*و\s*ربع)\b", text_clean):
            duration_seconds += 4500
            text_clean = re.sub(r"\b(?:ساعة\s*و\s*ربع|ساعة\s*وربع|ساعه\s*وربع|ساعه\s*و\s*ربع)\b", " ", text_clean)
        elif re.search(r"\b(?:ساعة\s*و\s*ثلث|ساعة\s*وثلث|ساعه\s*وثلث|ساعه\s*و\s*ثلث)\b", text_clean):
            duration_seconds += 4800
            text_clean = re.sub(r"\b(?:ساعة\s*و\s*ثلث|ساعة\s*وثلث|ساعه\s*وثلث|ساعه\s*و\s*ثلث)\b", " ", text_clean)

        # 2. Fractional hour phrases
        if re.search(r"\b(?:نصف\s*ساعة|نص\s*ساعة|نص\s*ساعه|نصف\s*ساعه)\b", text_clean):
            duration_seconds += 1800
            text_clean = re.sub(r"\b(?:نصف\s*ساعة|نص\s*ساعة|نص\s*ساعه|نصف\s*ساعه)\b", " ", text_clean)
        elif re.search(r"\b(?:ربع\s*ساعة|ربع\s*ساعه)\b", text_clean):
            duration_seconds += 900
            text_clean = re.sub(r"\b(?:ربع\s*ساعة|ربع\s*ساعه)\b", " ", text_clean)
        elif re.search(r"\b(?:ثلث\s*ساعة|ثلث\s*ساعه)\b", text_clean):
            duration_seconds += 1200
            text_clean = re.sub(r"\b(?:ثلث\s*ساعة|ثلث\s*ساعه)\b", " ", text_clean)

        # 3. Simple hour words
        if re.search(r"\b(?:ساعتين|ساعتان)\b", text_clean):
            duration_seconds += 7200
            text_clean = re.sub(r"\b(?:ساعتين|ساعتان)\b", " ", text_clean)
        elif re.search(r"\b(?:ساعة|ساعه)\b", text_clean):
            duration_seconds += 3600
            text_clean = re.sub(r"\b(?:ساعة|ساعه)\b", " ", text_clean)

        # 4. Minute phrases
        if re.search(r"\b(?:دقيقة\s*و\s*نصف|دقيقة\s*ونص|دقيقه\s*ونص|دقيقه\s*و\s*نصف)\b", text_clean):
            duration_seconds += 90
            text_clean = re.sub(
                r"\b(?:دقيقة\s*و\s*نصف|دقيقة\s*ونص|دقيقه\s*ونص|دقيقه\s*و\s*نصف)\b", " ", text_clean
            )
        elif re.search(r"\b(?:دقيقتين|دقيقتان)\b", text_clean):
            duration_seconds += 120
            text_clean = re.sub(r"\b(?:دقيقتين|دقيقتان)\b", " ", text_clean)
        elif re.search(r"\b(?:دقيقة|دقيقه)\b", text_clean) and not re.search(r"\d+\s*(?:دقيقة|دقيقه)", text_clean):
            duration_seconds += 60
            text_clean = re.sub(r"\b(?:دقيقة|دقيقه)\b", " ", text_clean)

        # 5. English phrases
        if re.search(r"\b(?:an\s+hour\s+and\s+a\s+half|1\.5\s+hours?)\b", text_clean, re.I):
            duration_seconds += 5400
            text_clean = re.sub(r"\b(?:an\s+hour\s+and\s+a\s+half|1\.5\s+hours?)\b", " ", text_clean, flags=re.I)
        elif re.search(r"\b(?:half\s+an\s+hour)\b", text_clean, re.I):
            duration_seconds += 1800
            text_clean = re.sub(r"\b(?:half\s+an\s+hour)\b", " ", text_clean, flags=re.I)
        elif re.search(r"\b(?:quarter\s+of\s+an\s+hour)\b", text_clean, re.I):
            duration_seconds += 900
            text_clean = re.sub(r"\b(?:quarter\s+of\s+an\s+hour)\b", " ", text_clean, flags=re.I)

        # Number + unit regex (Arabic & English)
        m_hr = re.search(r"(\d+)\s*(?:hours?|hrs?|ساعات|ساعة|ساعه)", text_clean, re.IGNORECASE)
        if m_hr:
            duration_seconds += int(m_hr.group(1)) * 3600
            text_clean = text_clean.replace(m_hr.group(0), " ")

        m_min = re.search(r"(\d+)\s*(?:minutes?|mins?|min|دقائق|دقيقة|دقيقه|دقايق)", text_clean, re.IGNORECASE)
        if m_min:
            duration_seconds += int(m_min.group(1)) * 60
            text_clean = text_clean.replace(m_min.group(0), " ")

        m_sec = re.search(r"(\d+)\s*(?:seconds?|secs?|sec|ثواني|ثوان|ثانية|ثانيه)", text_clean, re.IGNORECASE)
        if m_sec:
            duration_seconds += int(m_sec.group(1))
            text_clean = text_clean.replace(m_sec.group(0), " ")

        # Extract remaining action/title text
        clean_title = text_clean
        clean_title = re.sub(
            r"^(?:ممكن\s+)?(?:اضبط|حط|سوي|اعمل|شغل|عين|حدد)?\s*(?:مؤقت|منبه|تنبيه|تذكير|ذكرني|نبهني)?\s*"
            r"(?:بـ|ب|لـ|عن|على|ان|أني|اني)?\s*(?:بعد|لمدة|خلال)?\s*",
            "",
            clean_title,
            flags=re.IGNORECASE,
        )
        clean_title = re.sub(
            r"^(?:please\s+)?(?:set\s+a?\s*|create\s+a?\s*)?(?:timer|reminder|alarm)?\s*(?:for|in|to)?\s*",
            "",
            clean_title,
            flags=re.IGNORECASE,
        )
        clean_title = re.sub(r"\b(?:بعد|خلال|لمدة|in|for|to)\b", "", clean_title, flags=re.IGNORECASE)
        clean_title = re.sub(r"\s+", " ", clean_title).strip()

        return duration_seconds, clean_title

    @classmethod
    def parse_absolute_time(cls, text: str) -> Tuple[Optional[datetime], str]:
        """
        Parses Arabic/English clock times into a target datetime and title.
        e.g. 'ذكرني الساعة 4:30 عصراً بمكالمة العمل', 'at 5:15 pm meeting'.
        """
        now = datetime.now()
        target_dt = None
        clean_text = text.strip()

        # 1. Arabic format: الساعة HH(:MM)? (صباحاً|مساءً|عصراً|ظهراً|بالليل)?
        m_ar = re.search(
            r"(?:الساعة|ساعة|الساعه|ساعه)\s*(\d{1,2})(?::(\d{2}))?\s*"
            r"(صباحاً|صباحا|مساءً|مساء|عصراً|عصرا|ظهراً|ظهرا|بالليل)?",
            clean_text,
            re.I,
        )
        if m_ar:
            hr = int(m_ar.group(1))
            minute = int(m_ar.group(2)) if m_ar.group(2) else 0
            ampm = m_ar.group(3) or ""

            if ampm in ["مساءً", "مساء", "عصراً", "عصرا", "بالليل"] and hr < 12:
                hr += 12
            elif ampm in ["ظهراً", "ظهرا"] and hr < 12:
                hr += 12
            elif ampm in ["صباحاً", "صباحا"] and hr == 12:
                hr = 0
            elif not ampm and hr <= 11 and hr < now.hour:
                hr += 12

            target_dt = now.replace(hour=hr, minute=minute, second=0, microsecond=0)
            if target_dt <= now:
                target_dt += timedelta(days=1)

            clean_text = clean_text.replace(m_ar.group(0), " ")

        # 2. English format: at HH(:MM)? (am|pm)?
        if not target_dt:
            m_en = re.search(r"\b(?:at\s+)?(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", clean_text, re.I)
            if m_en:
                hr = int(m_en.group(1))
                minute = int(m_en.group(2)) if m_en.group(2) else 0
                ampm = m_en.group(3).lower()
                if ampm == "pm" and hr < 12:
                    hr += 12
                elif ampm == "am" and hr == 12:
                    hr = 0
                target_dt = now.replace(hour=hr, minute=minute, second=0, microsecond=0)
                if target_dt <= now:
                    target_dt += timedelta(days=1)

                clean_text = clean_text.replace(m_en.group(0), " ")

        # Clean title
        clean_title = re.sub(
            r"^(?:ممكن\s+)?(?:اضبط|حط|سوي|اعمل|شغل|عين|حدد)?\s*(?:منبه|تنبيه|تذكير|ذكرني|نبهني)?\s*"
            r"(?:بـ|ب|لـ|عن|على|ان|أني|اني)?\s*",
            "",
            clean_text,
            flags=re.IGNORECASE,
        )
        clean_title = re.sub(
            r"^(?:please\s+)?(?:set\s+a?\s*|create\s+a?\s*)?(?:reminder|alarm)?\s*(?:to|for)?\s*",
            "",
            clean_title,
            flags=re.IGNORECASE,
        )
        clean_title = re.sub(r"\s+", " ", clean_title).strip()

        return target_dt, clean_title

    def create_timer(self, duration_seconds: int, title: str = "") -> ReminderItem:
        """Creates a countdown timer due after duration_seconds."""
        self._init_schema()
        now = datetime.now()
        due_dt = now + timedelta(seconds=duration_seconds)
        rem_id = f"timer_{uuid.uuid4().hex[:8]}"

        display_title = title.strip() if title.strip() else f"مؤقت {duration_seconds // 60} دقيقة"
        due_str = due_dt.strftime("%H:%M:%S")

        item = ReminderItem(
            id=rem_id,
            title=display_title,
            due_timestamp=due_dt.timestamp(),
            due_time_str=due_str,
            duration_seconds=duration_seconds,
            remind_type="timer",
            status="active",
            created_at=now.isoformat(),
        )

        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO reminders (id, title, due_timestamp, due_time_str, duration_seconds, remind_type, status)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    item.id,
                    item.title,
                    item.due_timestamp,
                    item.due_time_str,
                    item.duration_seconds,
                    item.remind_type,
                    item.status,
                ),
            )

        logger.info("Created timer '%s' [%s] due at %s (%ds)", item.title, item.id, due_str, duration_seconds)
        return item

    def create_reminder(self, due_dt: datetime, title: str = "") -> ReminderItem:
        """Creates an absolute clock reminder/alarm."""
        self._init_schema()
        rem_id = f"rem_{uuid.uuid4().hex[:8]}"
        display_title = title.strip() if title.strip() else "تنبيه"
        due_str = due_dt.strftime("%Y-%m-%d %H:%M:%S")

        item = ReminderItem(
            id=rem_id,
            title=display_title,
            due_timestamp=due_dt.timestamp(),
            due_time_str=due_str,
            duration_seconds=0,
            remind_type="reminder",
            status="active",
            created_at=datetime.now().isoformat(),
        )

        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO reminders (id, title, due_timestamp, due_time_str, duration_seconds, remind_type, status)
                VALUES (?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    item.id,
                    item.title,
                    item.due_timestamp,
                    item.due_time_str,
                    item.duration_seconds,
                    item.remind_type,
                    item.status,
                ),
            )

        logger.info("Created reminder '%s' [%s] due at %s", item.title, item.id, due_str)
        return item

    def list_reminders(self, status: Optional[str] = "active") -> List[ReminderItem]:
        """Lists stored reminders and timers filtered by status."""
        self._init_schema()
        with self.db.get_connection() as conn:
            if status:
                rows = conn.execute(
                    """
                    SELECT id, title, due_timestamp, due_time_str, duration_seconds, remind_type, status, created_at
                    FROM reminders
                    WHERE status = ?
                    ORDER BY due_timestamp ASC;
                    """,
                    (status,),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT id, title, due_timestamp, due_time_str, duration_seconds, remind_type, status, created_at
                    FROM reminders
                    ORDER BY created_at DESC LIMIT 50;
                    """
                ).fetchall()

            return [
                ReminderItem(
                    id=r[0],
                    title=r[1],
                    due_timestamp=r[2],
                    due_time_str=r[3],
                    duration_seconds=r[4],
                    remind_type=r[5],
                    status=r[6],
                    created_at=str(r[7]),
                )
                for r in rows
            ]

    def cancel_reminder(self, reminder_id: Optional[str] = None) -> bool:
        """Cancels a specific reminder or the most recently created active timer."""
        self._init_schema()
        with self.db.get_connection() as conn:
            if reminder_id:
                conn.execute("UPDATE reminders SET status = 'cancelled' WHERE id = ?;", (reminder_id,))
                logger.info("Cancelled reminder ID: %s", reminder_id)
                return True

            # Cancel latest active timer/reminder
            row = conn.execute(
                "SELECT id FROM reminders WHERE status = 'active' ORDER BY created_at DESC LIMIT 1;"
            ).fetchone()
            if row:
                conn.execute("UPDATE reminders SET status = 'cancelled' WHERE id = ?;", (row[0],))
                logger.info("Cancelled latest active reminder ID: %s", row[0])
                return True
        return False

    def check_due_reminders(self) -> List[ReminderItem]:
        """Polls active reminders whose due_timestamp has arrived, marks them completed, and returns them."""
        self._init_schema()
        now_ts = time.time()
        due_items: List[ReminderItem] = []

        with self.db.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT id, title, due_timestamp, due_time_str, duration_seconds, remind_type, status, created_at
                FROM reminders
                WHERE status = 'active' AND due_timestamp <= ?
                ORDER BY due_timestamp ASC;
                """,
                (now_ts,),
            ).fetchall()

            for r in rows:
                item = ReminderItem(
                    id=r[0],
                    title=r[1],
                    due_timestamp=r[2],
                    due_time_str=r[3],
                    duration_seconds=r[4],
                    remind_type=r[5],
                    status="completed",
                    created_at=str(r[7]),
                )
                due_items.append(item)
                conn.execute("UPDATE reminders SET status = 'completed' WHERE id = ?;", (item.id,))

        return due_items

    async def trigger_alert(self, reminder: ReminderItem) -> None:
        """Dispatches audio chimes, native Windows toast, and HUD WebSocket broadcasts."""
        logger.info("⏰ ALERT TRIGGERED: %s [%s] (%s)", reminder.title, reminder.id, reminder.due_time_str)

        # 1. Windows Sound Chime
        try:
            import winsound

            winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
        except Exception as exc:
            logger.debug("winsound chime error: %s", exc)

        # 2. Native Windows Notification Toast
        try:
            from aegis_core.desktop.tray import tray_manager

            title_prefix = "⏳ مؤقت (Timer)" if reminder.remind_type == "timer" else "⏰ منبه (Reminder)"
            tray_manager.notify(
                title=f"{title_prefix}: {reminder.title}",
                message=f"حان موعد التنبيه الآن: {reminder.title}\nالتوقيت: {reminder.due_time_str}",
            )
        except Exception as exc:
            logger.debug("Tray notification alert error: %s", exc)

        # 3. Live WebSocket HUD Broadcast
        try:
            from aegis_core.api.websocket import broadcast_ws_event

            await broadcast_ws_event({
                "type": "reminder_alert",
                "reminder": reminder.to_dict(),
            })
        except Exception as exc:
            logger.debug("WebSocket reminder alert broadcast error: %s", exc)


reminder_manager = ReminderManager()
