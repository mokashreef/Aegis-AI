"""
Aegis AI - Quick Notes & Daily Log Manager.
Provides persistent, local, zero-cloud Markdown daily notes and fuzzy keyword search.
"""

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List
from aegis_core.config import settings
from aegis_core.utils.logger import logger


class NotesManager:
    """Manages local markdown daily notes and note search."""

    @classmethod
    def _get_notes_dir(cls) -> Path:
        notes_dir = settings.storage_dir / "notes"
        notes_dir.mkdir(parents=True, exist_ok=True)
        return notes_dir

    @classmethod
    def append_daily_note(cls, text: str) -> Dict[str, Any]:
        """Appends a timestamped note entry to today's daily log (YYYY-MM-DD.md)."""
        clean = text.strip()
        if not clean:
            return {"success": False, "error": "Note text cannot be empty."}

        now = datetime.now()
        date_str = now.strftime("%Y-%m-%d")
        time_str = now.strftime("%H:%M:%S")

        notes_dir = cls._get_notes_dir()
        note_file = notes_dir / f"{date_str}.md"

        is_new = not note_file.exists()
        header = f"# Daily Notes - {date_str}\n\n" if is_new else ""
        entry = f"{header}- **[{time_str}]**: {clean}\n"

        with open(note_file, "a", encoding="utf-8") as f:
            f.write(entry)

        logger.info("Appended note to %s: '%s'", note_file.name, clean)
        return {
            "success": True,
            "file": str(note_file.resolve()),
            "date": date_str,
            "time": time_str,
            "text": clean,
            "message": f"Saved note to {date_str}.md",
        }

    @classmethod
    def get_today_notes(cls) -> Dict[str, Any]:
        """Reads and returns the full content of today's notes."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        notes_dir = cls._get_notes_dir()
        note_file = notes_dir / f"{date_str}.md"

        if not note_file.exists():
            return {
                "success": True,
                "date": date_str,
                "content": "",
                "entries_count": 0,
                "message": f"No notes recorded yet for today ({date_str}).",
            }

        content = note_file.read_text(encoding="utf-8")
        lines = [ln for ln in content.splitlines() if ln.strip().startswith("- **[")]
        return {
            "success": True,
            "date": date_str,
            "content": content,
            "entries_count": len(lines),
            "message": f"Retrieved {len(lines)} entries from today's notes.",
        }

    @classmethod
    def search_notes(cls, query: str) -> Dict[str, Any]:
        """Searches all daily markdown notes for the query keyword."""
        q = query.lower().strip()
        if not q:
            return {"success": False, "error": "Query cannot be empty.", "matches": []}

        notes_dir = cls._get_notes_dir()
        matches: List[Dict[str, Any]] = []

        for md_file in sorted(notes_dir.glob("*.md"), reverse=True):
            try:
                lines = md_file.read_text(encoding="utf-8").splitlines()
                for idx, line in enumerate(lines):
                    if q in line.lower():
                        matches.append({
                            "date": md_file.stem,
                            "file": md_file.name,
                            "line_number": idx + 1,
                            "snippet": line.strip(),
                        })
            except Exception as exc:
                logger.debug("Error reading note file %s: %s", md_file.name, exc)

        return {
            "success": True,
            "query": query,
            "matches_count": len(matches),
            "matches": matches,
            "message": f"Found {len(matches)} match(es) for '{query}'.",
        }


# Global notes manager singleton
notes_manager = NotesManager()
