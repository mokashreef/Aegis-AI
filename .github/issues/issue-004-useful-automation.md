# Issue #4: Useful Automation (Fuzzy App Matcher, Natural Language Intent & Window Management)

- **Labels**: `enhancement`, `automation`, `desktop`, `win32`, `mvp`, `p0`
- **Milestone**: MVP Recovery (Phase 4)
- **Status**: RESOLVED (Completed & Verified)
- **Branch**: `feat/phase4-useful-automation`

## Resolution Summary
1. **Fuzzy Application Discovery (`backend/aegis_core/automation/app_finder.py`)**:
   - Indexes Start Menu (`.lnk`), Windows Registry `App Paths` (`HKLM`/`HKCU`), and built-in system tools.
   - Robust scoring engine resolves "open chrome", "launch google chrome", "can you start notepad please", "calc", "vscode" to executable paths and launches via native `os.startfile` or detached process.
2. **Natural Language Intent Router (`backend/aegis_core/automation/intent_router.py`)**:
   - Zero-latency entity extraction and classification for app launches, app termination, window operations, system specs, and clipboard actions.
3. **Native Window Management (`backend/aegis_core/automation/window_manager.py`)**:
   - Win+D Show Desktop simulation (`minimize_all`).
   - Monitor work area aware snapping (`snap_window` left/right/maximize).
   - Fuzzy window focusing (`focus_window_by_title`).
4. **Agent Integration & Direct Feedback**:
   - Integrated into `AgentPlanner` replacing brittle `startswith("open ")`.
   - Guaranteed natural user response even if local LLM is offline.
5. **Testing**:
   - 27/27 unit & integration tests passing (`test_automation.py`).
   - `flake8 backend` with 0 warnings.

## Problem Statement
The existing desktop automation is rigid and brittle:
1. It relies on strict string prefixes like `text.startswith("open ")`, failing completely when users say natural phrases like "launch google chrome", "can you start notepad please", or "run calculator".
2. Application discovery is hardcoded or relies only on literal PATH execution, failing to find apps installed in Start Menu directories or registered in Windows Registry App Paths.
3. Window management capabilities (minimize all, bring to front, tile left/right) are either stubs or non-existent.

## Scope & Acceptance Criteria
1. **Fuzzy Application Discovery & Matcher (`app_finder.py`)**:
   - Enumerate Start Menu shortcuts (`User` and `All Users`), Windows Registry `App Paths`, and standard system directories.
   - Implement fuzzy similarity scoring (token similarity, subsequence match, Levenshtein ratio) to resolve natural app names to executable targets.
   - Accurately resolve "chrome", "google chrome", "notepad", "calculator", "calc", "vscode", "visual studio code", "explorer", "settings", "cmd", "terminal".
2. **Natural Language Intent Extraction (`intent_router.py`)**:
   - Classify user queries into actionable intents without requiring external cloud APIs:
     - `APP_LAUNCH`: "open X", "launch X", "start X", "run X", "can you open X please"
     - `APP_CLOSE`: "close X", "kill X", "exit X", "terminate X"
     - `WINDOW_ACTION`: "minimize all", "show desktop", "focus X", "snap left", "snap right"
     - `SYSTEM_QUERY`: "system info", "cpu usage", "memory status"
     - `CONVERSATION`: standard conversational / reasoning requests routed to AI LLM.
3. **Native Window Management (`window_manager.py`)**:
   - Minimize all / Show desktop via COM `Shell.Application` or Win32 `keybd_event` (Win+M / Win+D).
   - Bring target application window to foreground (`SetForegroundWindow`, `ShowWindow`).
   - Window snapping (tile left, tile right, maximize) using Win32 API and active monitor bounds.
4. **Automated Verification**:
   - High test coverage for app indexing, fuzzy resolution, intent extraction, and window operations.
   - Zero flake8 warnings and all tests passing.
