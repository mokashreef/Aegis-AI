"""
Aegis AI - Built-in Desktop Automation Tools.
Wraps Windows process, window, volume, brightness, screen capture, quick notes,
and URL/browser opening as BaseTool implementations.
"""

from typing import Any
import urllib.parse
import webbrowser
from aegis_core.automation.brightness_manager import brightness_manager
from aegis_core.automation.clipboard_manager import ClipboardManager
from aegis_core.automation.notes_manager import notes_manager
from aegis_core.automation.process_manager import ProcessManager
from aegis_core.automation.screen_capture import screen_capture
from aegis_core.automation.volume_manager import volume_manager
from aegis_core.automation.window_manager import WindowManager
from aegis_core.plugins.base import BaseTool, RiskLevel, ToolResult
from aegis_core.utils.logger import logger
from aegis_core.utils.system_info import get_system_telemetry


class LaunchAppTool(BaseTool):
    name = "launch_application"
    description = (
        "Launches a Windows desktop application or utility using fuzzy matching "
        "(e.g. 'chrome', 'google chrome', 'notepad', 'calculator', 'terminal', 'vs code')."
    )
    risk_level = RiskLevel.MUTATING_SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "app_name": {
                "type": "string",
                "description": "The application name or command (e.g., 'chrome', 'notepad', 'calculator').",
            },
        },
        "required": ["app_name"],
    }

    async def execute(self, app_name: str, **kwargs: Any) -> ToolResult:
        res = ProcessManager.launch_app(app_name)
        if res.get("launched"):
            return ToolResult(
                success=True,
                data=res,
                message=f"Successfully launched {res.get('name', app_name)}",
            )

        # Defensive fallback: If app_name contains website keywords, redirect to OpenUrlTool
        web_indicators = [
            "موقع", "صفحة", "دوت", ".com", ".net", ".org", " و افتح ", "وافتح", "http://", "https://",
        ]
        lower_app = app_name.lower()
        if any(ind in lower_app for ind in web_indicators):
            logger.info("LaunchAppTool intercepted website intent in '%s' - redirecting to OpenUrlTool.", app_name)
            browser = ""
            for b_name in ["chrome", "كروم", "comet", "كومت", "edge", "ايدج", "brave", "بريف", "firefox", "فايرفوكس"]:
                if b_name in lower_app:
                    browser = b_name
                    break
            clean_url = app_name
            tokens_to_clean = [
                "المتصفح", "متصفح", "موقع", "صفحة", "وافتح", "افتح", "شغل",
                "كروم", "كومت", "ايدج", "بريف", "فايرفوكس", " و ", " و", "و ",
            ]
            for rm in tokens_to_clean:
                clean_url = clean_url.replace(rm, " ")
            clean_url = clean_url.strip()
            if clean_url.startswith("ال "):
                clean_url = clean_url[3:].strip()
            from aegis_core.automation.intent_router import normalize_spoken_arabic_text

            clean_url = normalize_spoken_arabic_text(clean_url)
            url_tool = OpenUrlTool()
            return await url_tool.execute(url=clean_url or app_name, browser=browser)

        return ToolResult(
            success=False,
            error=res.get("error", f"Failed to launch application '{app_name}'."),
            data=res,
        )


class OpenUrlTool(BaseTool):
    name = "open_url"
    description = (
        "Opens a website URL, domain, or web search query in a desktop browser (e.g. Chrome, Edge, Brave, Comet). "
        "Automatically ensures https:// protocol."
    )
    risk_level = RiskLevel.MUTATING_SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "Website URL, domain, or search query (e.g. 'https://youtube.com', 'google.com').",
            },
            "browser": {
                "type": "string",
                "description": "Optional specific browser name (e.g. 'chrome', 'msedge', 'brave', 'comet', 'firefox').",
            },
        },
        "required": ["url"],
    }

    async def execute(self, url: str, browser: str = "", **kwargs: Any) -> ToolResult:
        target_url = url.strip()
        low = target_url.lower()

        KNOWN_URLS = {
            "youtube": "https://www.youtube.com",
            "يوتيوب": "https://www.youtube.com",
            "google": "https://www.google.com",
            "جوجل": "https://www.google.com",
            "غوغل": "https://www.google.com",
            "github": "https://www.github.com",
            "جيت هاب": "https://www.github.com",
            "غيتهاب": "https://www.github.com",
            "twitter": "https://x.com",
            "تويتر": "https://x.com",
            "facebook": "https://www.facebook.com",
            "فيسبوك": "https://www.facebook.com",
            "chatgpt": "https://chatgpt.com",
            "شات جي بي تي": "https://chatgpt.com",
            "gmail": "https://mail.google.com",
            "جيميل": "https://mail.google.com",
        }

        if low in KNOWN_URLS:
            target_url = KNOWN_URLS[low]
        elif not target_url.startswith("http://") and not target_url.startswith("https://"):
            if "." in target_url and " " not in target_url:
                target_url = f"https://{target_url}"
            else:
                target_url = f"https://www.google.com/search?q={urllib.parse.quote_plus(target_url)}"

        browser_choice = browser.strip().lower()
        if not browser_choice:
            try:
                from aegis_core.memory.session_manager import session_manager

                pref_browser = session_manager.get_preference("default_browser", "chrome")
                if pref_browser and pref_browser != "default":
                    browser_choice = pref_browser.strip().lower()
            except Exception:
                pass

        BROWSER_MAP = {
            "chrome": "chrome",
            "كروم": "chrome",
            "جوجل كروم": "chrome",
            "edge": "msedge",
            "msedge": "msedge",
            "ايدج": "msedge",
            "مايكروسوفت ايدج": "msedge",
            "brave": "brave",
            "بريف": "brave",
            "comet": "comet",
            "كومت": "comet",
            "firefox": "firefox",
            "فايرفوكس": "firefox",
        }
        target_browser = BROWSER_MAP.get(browser_choice, browser_choice)

        opened = False
        method = "default_browser"

        if target_browser and target_browser != "default":
            try:
                launch_res = ProcessManager.launch_app(target_browser, [target_url])
                if launch_res.get("launched"):
                    opened = True
                    method = f"browser_{target_browser}"
            except Exception as exc:
                logger.debug("Specific browser launch failed: %s", exc)

        if not opened:
            try:
                webbrowser.open(target_url)
                opened = True
            except Exception as exc:
                return ToolResult(success=False, error=f"Failed to open URL '{target_url}': {exc}")

        return ToolResult(
            success=True,
            data={"url": target_url, "browser": target_browser or "default", "method": method},
            message=f"Opened {target_url} in {target_browser or 'default browser'}",
        )


class CloseAppTool(BaseTool):
    name = "close_application"
    description = "Terminates a running Windows desktop application by executable name or process ID."
    risk_level = RiskLevel.RESTRICTED_CONFIRM
    parameters_schema = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Process name to terminate (e.g. 'notepad.exe', 'calc.exe', 'chrome.exe').",
            },
            "pid": {
                "type": "integer",
                "description": "Optional specific process ID to terminate.",
            },
        },
    }

    async def execute(self, name: str = "", pid: int = 0, **kwargs: Any) -> ToolResult:
        p_name = name if name else None
        p_id = pid if pid > 0 else None
        res = ProcessManager.terminate_process(pid=p_id, name=p_name)
        if res.get("success"):
            return ToolResult(success=True, data=res)
        return ToolResult(
            success=False,
            error=res.get("error", f"Failed to terminate process {name or pid}."),
            data=res,
        )


class ListProcessesTool(BaseTool):
    name = "list_processes"
    description = "Retrieves currently active Windows desktop processes sorted by memory usage."
    risk_level = RiskLevel.READ_ONLY
    parameters_schema = {
        "type": "object",
        "properties": {
            "filter_name": {
                "type": "string",
                "description": "Optional string filter to match process names.",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of processes to return (default 25).",
            },
        },
    }

    async def execute(self, filter_name: str = "", limit: int = 25, **kwargs: Any) -> ToolResult:
        fname = filter_name if filter_name else None
        procs = ProcessManager.list_processes(filter_name=fname, limit=limit)
        return ToolResult(success=True, data={"processes": procs, "count": len(procs)})


class GetClipboardTool(BaseTool):
    name = "get_clipboard"
    description = "Reads current text content from the Windows clipboard."
    risk_level = RiskLevel.READ_ONLY
    parameters_schema = {"type": "object", "properties": {}}

    async def execute(self, **kwargs: Any) -> ToolResult:
        text = ClipboardManager.get_text()
        return ToolResult(
            success=True,
            data={"text": text, "length": len(text)},
            message=f"Clipboard content: {text[:100]}..." if len(text) > 100 else f"Clipboard: {text}",
        )


class SetClipboardTool(BaseTool):
    name = "set_clipboard"
    description = "Overwrites the Windows clipboard with the provided text."
    risk_level = RiskLevel.MUTATING_SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Text to write to the clipboard.",
            },
        },
        "required": ["text"],
    }

    async def execute(self, text: str, **kwargs: Any) -> ToolResult:
        success = ClipboardManager.set_text(text)
        return ToolResult(success=success, data={"length": len(text)})


class ListWindowsTool(BaseTool):
    name = "list_windows"
    description = "Lists all visible, top-level application windows on the desktop."
    risk_level = RiskLevel.READ_ONLY
    parameters_schema = {"type": "object", "properties": {}}

    async def execute(self, **kwargs: Any) -> ToolResult:
        wins = WindowManager.list_windows()
        return ToolResult(success=True, data={"windows": wins, "count": len(wins)})


class FocusWindowTool(BaseTool):
    name = "focus_window"
    description = "Brings a window into the foreground using its HWND window handle."
    risk_level = RiskLevel.MUTATING_SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "hwnd": {
                "type": "integer",
                "description": "Window handle integer identifier.",
            },
        },
        "required": ["hwnd"],
    }

    async def execute(self, hwnd: int, **kwargs: Any) -> ToolResult:
        success = WindowManager.focus_window(hwnd)
        return ToolResult(success=success, data={"hwnd": hwnd})


class FocusWindowByTitleTool(BaseTool):
    name = "focus_window_by_title"
    description = "Finds and brings an application window into the foreground using fuzzy title matching."
    risk_level = RiskLevel.MUTATING_SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "title": {
                "type": "string",
                "description": "App or window title to match (e.g. 'Notepad', 'Chrome', 'Visual Studio Code').",
            },
        },
        "required": ["title"],
    }

    async def execute(self, title: str = "", title_query: str = "", **kwargs: Any) -> ToolResult:
        query = title or title_query
        res = WindowManager.focus_window_by_title(query)
        if res.get("focused") or res.get("success"):
            return ToolResult(
                success=True,
                data=res,
                message=f"Brought window '{res.get('title')}' to front.",
            )
        return ToolResult(
            success=False,
            error=res.get("error", f"No window matching '{query}' was found."),
            data=res,
        )


class MinimizeAllWindowsTool(BaseTool):
    name = "minimize_all_windows"
    description = "Simulates Show Desktop (Win+D) to minimize all open application windows."
    risk_level = RiskLevel.MUTATING_SAFE
    parameters_schema = {"type": "object", "properties": {}}

    async def execute(self, **kwargs: Any) -> ToolResult:
        success = WindowManager.minimize_all()
        return ToolResult(success=success, message="All windows minimized (Show Desktop triggered).")


class SnapWindowTool(BaseTool):
    name = "snap_window"
    description = "Snaps the foreground active window to the 'left' or 'right' half of the monitor, or maximizes it."
    risk_level = RiskLevel.MUTATING_SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "side": {
                "type": "string",
                "enum": ["left", "right", "maximize", "restore"],
                "description": "Placement layout target.",
            },
            "hwnd": {
                "type": "integer",
                "description": "Optional specific window handle to snap. If omitted, uses current foreground window.",
            },
        },
        "required": ["side"],
    }

    async def execute(self, side: str, hwnd: int = 0, **kwargs: Any) -> ToolResult:
        h = hwnd if hwnd > 0 else None
        res = WindowManager.snap_window(side=side, hwnd=h)
        if res.get("snapped") or res.get("success"):
            return ToolResult(
                success=True,
                data=res,
                message=f"Snapped window to {side}.",
            )
        return ToolResult(
            success=False,
            error=res.get("error", f"Failed to snap window to {side}."),
            data=res,
        )


class VolumeControlTool(BaseTool):
    name = "control_volume"
    description = (
        "Controls Windows master audio volume: set level (0-100), mute, unmute, "
        "or relatively adjust volume up/down."
    )
    risk_level = RiskLevel.MUTATING_SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["set", "mute", "unmute", "increase", "decrease", "status"],
                "description": "Volume action to perform.",
            },
            "level": {
                "type": "integer",
                "description": "Target volume percentage (0-100) or step amount for increase/decrease.",
            },
        },
        "required": ["action"],
    }

    async def execute(self, action: str, level: int = 0, **kwargs: Any) -> ToolResult:
        act = action.lower().strip()
        if act == "set":
            res = volume_manager.set_volume(level)
        elif act == "mute":
            res = volume_manager.mute()
        elif act == "unmute":
            res = volume_manager.unmute()
        elif act == "increase":
            res = volume_manager.change_volume(step=level if level > 0 else 10)
        elif act == "decrease":
            res = volume_manager.change_volume(step=-(level if level > 0 else 10))
        elif act == "status":
            res = volume_manager.get_status()
        else:
            return ToolResult(success=False, error=f"Unknown volume action '{action}'.")

        return ToolResult(
            success=res.get("success", True),
            data=res,
            message=res.get("message", f"Volume action {action} completed."),
        )


class BrightnessControlTool(BaseTool):
    name = "control_brightness"
    description = (
        "Controls primary display brightness on supported Windows laptops/monitors: "
        "set percentage (0-100), increase, decrease, or query current level."
    )
    risk_level = RiskLevel.MUTATING_SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["set", "increase", "decrease", "status"],
                "description": "Brightness action to perform.",
            },
            "level": {
                "type": "integer",
                "description": "Target percentage (0-100) or step amount for relative adjustment.",
            },
        },
        "required": ["action"],
    }

    async def execute(self, action: str, level: int = 0, **kwargs: Any) -> ToolResult:
        act = action.lower().strip()
        if act == "set":
            res = brightness_manager.set_brightness(level)
        elif act in ["increase", "up"]:
            delta = level if level > 0 else 10
            res = brightness_manager.adjust_brightness(delta)
        elif act in ["decrease", "down"]:
            delta = level if level > 0 else 10
            res = brightness_manager.adjust_brightness(-delta)
        elif act in ["get", "status"]:
            res = brightness_manager.get_brightness()
        else:
            return ToolResult(success=False, error=f"Unknown brightness action '{action}'.")

        return ToolResult(
            success=res.get("success", False),
            data=res,
            message=res.get("message", f"Brightness action {action} completed."),
        )


class ScreenCaptureTool(BaseTool):
    name = "capture_screen"
    description = (
        "Captures the Windows desktop screen and encodes the result in base64 "
        "for instant multimodal agent context."
    )
    risk_level = RiskLevel.READ_ONLY
    parameters_schema = {
        "type": "object",
        "properties": {
            "target": {
                "type": "string",
                "enum": ["full", "window"],
                "description": "Target capture boundary.",
            },
        },
    }

    async def execute(self, target: str = "full", **kwargs: Any) -> ToolResult:
        res = screen_capture.capture(target=target)
        if res.get("success"):
            return ToolResult(
                success=True,
                data={
                    "path": res.get("path"),
                    "size_bytes": res.get("size_bytes"),
                    "latency_ms": res.get("latency_ms"),
                    "width": res.get("width"),
                    "height": res.get("height"),
                    "base64_preview": res.get("base64", "")[:60] + "...",
                },
                message=res.get("message", "Screen captured successfully."),
            )
        return ToolResult(success=False, error="Screen capture failed.", data=res)


class AnalyzeScreenTool(BaseTool):
    name = "analyze_screen"
    description = (
        "Captures and intelligently analyzes what is currently displayed on the Windows desktop "
        "(Ask My Screen / Vision AI), identifying active applications, window contents, and key elements."
    )
    risk_level = RiskLevel.READ_ONLY
    parameters_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Specific question or instruction about what is shown on the screen.",
            },
            "target": {
                "type": "string",
                "enum": ["full", "window"],
                "description": "Capture target area (default: 'full').",
            },
        },
    }

    async def execute(self, query: str = "", target: str = "full", **kwargs: Any) -> ToolResult:
        from aegis_core.ai_runtime.vision_analyzer import screen_vision_analyzer

        res = await screen_vision_analyzer.analyze_screen(query=query, target=target)
        if res.get("success"):
            return ToolResult(
                success=True,
                data={
                    "active_window": res.get("active_window"),
                    "resolution": res.get("resolution"),
                    "screenshot_path": res.get("screenshot_path"),
                    "screenshot_url": res.get("screenshot_url"),
                    "latency_ms": res.get("latency_ms"),
                    "vision_model_used": res.get("vision_model_used"),
                    "has_local_vision_model": res.get("has_local_vision_model"),
                    "open_windows": res.get("open_windows"),
                },
                message=res.get("analysis", "Screen analyzed successfully."),
            )
        return ToolResult(success=False, error=res.get("error", "Vision screen analysis failed."), data=res)


class QuickNotesTool(BaseTool):
    name = "manage_notes"
    description = (
        "Manages local markdown daily notes: 'append' to today's note, 'search' notes, or 'read_today'."
    )
    risk_level = RiskLevel.MUTATING_SAFE
    parameters_schema = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["append", "read_today", "search"],
                "description": "Notes operation to perform.",
            },
            "text": {
                "type": "string",
                "description": "Note content to append or search text.",
            },
            "query": {
                "type": "string",
                "description": "Search keyword when action is 'search'.",
            },
        },
        "required": ["action"],
    }

    async def execute(self, action: str, text: str = "", query: str = "", **kwargs: Any) -> ToolResult:
        act = action.lower().strip()
        if act == "append":
            res = notes_manager.append_daily_note(text)
            return ToolResult(success=res.get("success", False), data=res, message=res.get("message"))
        elif act in ["read_today", "read"]:
            res = notes_manager.get_today_notes()
            return ToolResult(success=res.get("success", True), data=res, message=res.get("message"))
        elif act == "search":
            res = notes_manager.search_notes(query or text)
            return ToolResult(success=res.get("success", False), data=res, message=res.get("message"))
        return ToolResult(success=False, error=f"Unknown notes action '{action}'.")


class GetSystemTelemetryTool(BaseTool):
    name = "get_system_telemetry"
    description = "Retrieves Windows system information including CPU usage, RAM utilization, and OS version."
    risk_level = RiskLevel.READ_ONLY
    parameters_schema = {"type": "object", "properties": {}}

    async def execute(self, **kwargs: Any) -> ToolResult:
        info = get_system_telemetry()
        return ToolResult(success=True, data=info)
