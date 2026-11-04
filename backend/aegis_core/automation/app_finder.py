"""
Aegis AI - Windows Application Discovery & Fuzzy Matcher.
Indexes Start Menu shortcuts, Registry App Paths, and standard Windows system executables,
matching natural user requests (e.g. 'launch google chrome', 'open calc') to executable targets.
"""

from difflib import SequenceMatcher
import os
from pathlib import Path
import re
import subprocess
import time
from typing import Any, Dict, List, Optional
from aegis_core.utils.logger import logger

try:
    import winreg
except ImportError:
    winreg = None


KNOWN_SYSTEM_APPS: Dict[str, str] = {
    "notepad": "notepad.exe",
    "notes": "notepad.exe",
    "calculator": "calc.exe",
    "calc": "calc.exe",
    "paint": "mspaint.exe",
    "mspaint": "mspaint.exe",
    "terminal": "wt.exe",
    "command prompt": "cmd.exe",
    "cmd": "cmd.exe",
    "powershell": "powershell.exe",
    "file explorer": "explorer.exe",
    "explorer": "explorer.exe",
    "task manager": "taskmgr.exe",
    "taskmgr": "taskmgr.exe",
    "control panel": "control.exe",
    "settings": "ms-settings:",
    "registry editor": "regedit.exe",
    "regedit": "regedit.exe",
    "edge": "msedge.exe",
    "microsoft edge": "msedge.exe",
    "wordpad": "write.exe",
    "remote desktop": "mstsc.exe",
    "cleanmgr": "cleanmgr.exe",
}


class AppCandidate:
    """Represents a discovered launchable application target."""

    def __init__(self, name: str, target: str, source: str):
        self.name = name
        self.clean_name = self._clean_name(name)
        self.target = target
        self.source = source

    @staticmethod
    def _clean_name(raw: str) -> str:
        s = raw.lower()
        s = re.sub(r"\.(exe|lnk|url|appref-ms)$", "", s)
        s = re.sub(r"[_\-\.\(\)]", " ", s)
        return " ".join(s.split())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "clean_name": self.clean_name,
            "target": self.target,
            "source": self.source,
        }


class AppFinder:
    """Discovers, indexes, and fuzzy matches Windows desktop applications."""

    def __init__(self, cache_ttl_seconds: int = 300):
        self.cache_ttl = cache_ttl_seconds
        self._last_scan_time = 0.0
        self._index: List[AppCandidate] = []

    def refresh_index(self, force: bool = False) -> None:
        """Refreshes the index from Start Menu, Registry, and standard system paths."""
        now = time.time()
        if not force and (now - self._last_scan_time) < self.cache_ttl and self._index:
            return

        candidates: Dict[str, AppCandidate] = {}

        # 1. Register known built-in system tools
        for alias, target in KNOWN_SYSTEM_APPS.items():
            candidates[f"sys:{alias}"] = AppCandidate(name=alias, target=target, source="system")

        # 2. Windows Registry App Paths (HKLM & HKCU)
        if winreg and os.name == "nt":
            hives = [
                (winreg.HKEY_LOCAL_MACHINE, "HKLM"),
                (winreg.HKEY_CURRENT_USER, "HKCU"),
            ]
            for hive, hname in hives:
                try:
                    key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths"
                    with winreg.OpenKey(hive, key_path) as parent_key:
                        num_subkeys = winreg.QueryInfoKey(parent_key)[0]
                        for i in range(num_subkeys):
                            try:
                                subkey_name = winreg.EnumKey(parent_key, i)
                                with winreg.OpenKey(parent_key, subkey_name) as subkey:
                                    val, _ = winreg.QueryValueEx(subkey, "")
                                    if val and Path(val).exists():
                                        app_key = f"reg:{subkey_name.lower()}"
                                        candidates[app_key] = AppCandidate(
                                            name=subkey_name,
                                            target=str(val),
                                            source=f"registry_{hname.lower()}",
                                        )
                            except Exception:
                                continue
                except Exception as exc:
                    logger.debug("Could not read registry app paths from %s: %s", hname, exc)

        # 3. Start Menu Shortcuts (.lnk)
        start_dirs = [
            Path(os.environ.get("APPDATA", "")) / "Microsoft/Windows/Start Menu/Programs",
            Path(os.environ.get("ALLUSERSPROFILE", "")) / "Microsoft/Windows/Start Menu/Programs",
            Path(os.environ.get("PROGRAMDATA", "")) / "Microsoft/Windows/Start Menu/Programs",
        ]

        for sdir in start_dirs:
            if sdir.exists():
                try:
                    for link_path in sdir.rglob("*.lnk"):
                        name = link_path.stem
                        clean = name.lower()
                        # Exclude uninstaller / documentation links
                        if any(kw in clean for kw in ["uninstall", "remove", "help", "readme", "documentation"]):
                            continue
                        app_key = f"lnk:{clean}"
                        if app_key not in candidates:
                            candidates[app_key] = AppCandidate(
                                name=name,
                                target=str(link_path.resolve()),
                                source="start_menu",
                            )
                except Exception as exc:
                    logger.debug("Error scanning start menu directory %s: %s", sdir, exc)

        self._index = list(candidates.values())
        self._last_scan_time = now
        logger.info("Application index populated with %d launchable targets.", len(self._index))

    def _score_similarity(self, query: str, candidate: AppCandidate) -> float:
        """Calculates a fuzzy match score (0.0 to 100.0) between query and candidate."""
        q = query.lower().strip()
        c = candidate.clean_name.lower().strip()

        # 1. Exact match
        if q == c:
            return 100.0

        # 2. Acronym match (e.g. "vscode" -> "visual studio code")
        words = c.split()
        if len(words) > 1:
            acronym = "".join(w[0] for w in words)
            if q == acronym:
                return 96.0

        # 3. Substring / Word inclusion
        if q in c:
            # Score higher if matching at word boundary
            return 90.0 + (len(q) / len(c)) * 8.0

        if c in q:
            return 85.0

        # 4. Token overlap
        q_tokens = set(q.split())
        c_tokens = set(c.split())
        if q_tokens and c_tokens:
            common = q_tokens.intersection(c_tokens)
            if common:
                overlap_ratio = len(common) / max(len(q_tokens), len(c_tokens))
                return 75.0 + overlap_ratio * 15.0

        # 5. Levenshtein / SequenceMatcher ratio
        seq_ratio = SequenceMatcher(None, q, c).ratio()
        return seq_ratio * 70.0

    def find_app(self, query: str, min_score: float = 60.0) -> Optional[Dict[str, Any]]:
        """Finds the best matching application candidate for a query string."""
        self.refresh_index()
        clean_query = query.lower().strip()

        # Remove polite filler words ("please", "can you", "start", "open", "launch", "run")
        clean_query = re.sub(
            r"^(please\s+|can\s+you\s+(please\s+)?(open|launch|start|run)\s+|open\s+|launch\s+|start\s+|run\s+)",
            "",
            clean_query,
        ).strip()
        clean_query = re.sub(r"\s+please$", "", clean_query).strip()

        if not clean_query:
            return None

        # Direct check against known system apps first
        if clean_query in KNOWN_SYSTEM_APPS:
            return {
                "name": clean_query,
                "target": KNOWN_SYSTEM_APPS[clean_query],
                "score": 100.0,
                "source": "system_direct",
            }

        best_candidate: Optional[AppCandidate] = None
        highest_score = 0.0

        for cand in self._index:
            score = self._score_similarity(clean_query, cand)
            if score > highest_score:
                highest_score = score
                best_candidate = cand

        if best_candidate and highest_score >= min_score:
            res = best_candidate.to_dict()
            res["score"] = round(highest_score, 1)
            return res

        return None

    def launch(self, query: str) -> Dict[str, Any]:
        """Resolves an application by query and executes it safely on Windows."""
        match = self.find_app(query)
        target = match["target"] if match else query.strip()
        matched_name = match["name"] if match else query.strip()
        score = match["score"] if match else 0.0

        logger.info("Launching target '%s' (matched: '%s', score: %.1f)", target, matched_name, score)

        try:
            # 1. Native Windows os.startfile handles .lnk, URL, and .exe seamlessly
            if os.name == "nt" and hasattr(os, "startfile"):
                os.startfile(target)
                return {
                    "success": True,
                    "target": target,
                    "name": matched_name,
                    "score": score,
                    "message": f"Successfully launched {matched_name}",
                }

            # 2. Subprocess fallback
            no_win = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            proc = subprocess.Popen(
                [target],
                shell=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL,
                creationflags=no_win,
            )
            return {
                "success": True,
                "target": target,
                "name": matched_name,
                "score": score,
                "pid": proc.pid,
                "message": f"Successfully launched {matched_name}",
            }
        except Exception as exc:
            logger.error("Failed launching '%s': %s", target, exc)
            return {
                "success": False,
                "target": target,
                "name": matched_name,
                "error": str(exc),
                "message": f"Failed to launch {matched_name}: {exc}",
            }


# Global app finder singleton
app_finder = AppFinder()

