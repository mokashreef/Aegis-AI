# Issue #14: Real Desktop Executable (.exe), Windows Startup Auto-Run, Normal Z-Order Layering, Spoken Domain NLP & Premium UI Redesign

- **Labels**: `desktop`, `packaging`, `startup`, `arabic`, `nlp`, `ui`, `ux`, `p1`
- **Milestone**: MVP Usability & System Integration
- **Status**: CLOSED
- **Branch**: `feat/native-app-arabic-nlp-ui-startup`

## Problem Analysis

User feedback following Phase 13 revealed key real-world challenges:

1. **Misrouted Spoken Arabic Commands**:
   - Saying `"كروم و افتح موقع كود التطور دوت نت"` routed to `launch_application` with `app_name="كروم و افتح موقع كود التطور دوت نت"`, causing immediate failure.
   - Users speak phonetic domain names (e.g. "دوت نت" for `.net`, "دوت كوم" for `.com`) and compound phrases ("افتح كروم وافتح موقع...").
   - `LaunchAppTool` lacked defensive fallback to web browsing when the target string resembles a website or web search.
2. **Aggressive Window Z-Order (TopMost Blocking)**:
   - Window defaulted to `on_top=True` (`WS_EX_TOPMOST`), preventing normal Windows z-order behavior (clicking Chrome or Codex didn't bring them over Aegis).
   - Default behavior must be normal window layering (`on_top=False`), allowing users to click other apps and have Aegis respect standard OS focus.
3. **Transcription Latency & Status Feedback**:
   - STT transcribing feels slow or hangs during processing. Need faster Whisper configuration (`tiny` / `base` optimized with CPU threads), VAD chunking refinement, and immediate optimistic visual feedback.
4. **UI Visual Polish & Layout Cramping**:
   - The companion card layout feels cramped ("فايت ببعضو") with heavy dark blocks and dense tool execution cards.
   - Needs a spacious, premium Windows 11 Fluent / macOS Spotlight layout with balanced margins, typography, sleek action cards, and clean visual hierarchy.
5. **Native Application (.exe) & Windows Startup Daemon**:
   - User requires a real desktop `.exe` application rather than a `.bat` script.
   - Aegis must register into Windows Startup (`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`) to start automatically with Windows in the background (minimized to system tray).

## Completed Deliverables

1. **Phonetic & Compound Arabic NLP in `intent_router.py`**:
   - Spoken domain normalization (`normalize_spoken_arabic_text`): Converts phonetic spoken domains ("دوت نت" $\rightarrow$ `.net`, "دوت كوم" $\rightarrow$ `.com`, "دوت اورج" $\rightarrow$ `.org`, etc.).
   - Compound sentence patterns (`m_ar_compound`, `m_ar_target_br`): Accurately routes "كروم و افتح موقع X" $\rightarrow$ `open_url(url="X", browser="chrome")`.
   - Defensive fallback in `LaunchAppTool`: Automatically intercepts website requests mistakenly sent to application launch and seamlessly delegates them to `OpenUrlTool`.
2. **Normal Window Layering by Default in `window.py` & `CompanionOverlay.tsx`**:
   - Default `_is_on_top = False` and `isPinned = false`. Aegis operates as a normal standard desktop window that naturally drops behind other applications (Chrome, VSCode, Codex) when clicked outside.
   - Pinned mode remains easily toggleable via header Pin button whenever user wishes to keep Aegis floating on top.
3. **Faster Whisper STT & VAD Chunking**:
   - Configured `condition_on_previous_text=False`, redundant VAD filter disabled in Faster-Whisper, and maximized CPU thread allocation.
   - Snappy trailing silence detection in `useMicrophoneCapture.ts` (900ms).
4. **UI Design Overhaul in `ActionCard.tsx` & `CompanionOverlay.tsx`**:
   - Expanded window size to 780x640 for a breathable, elegant feel.
   - Redesigned `ActionCard` with tool-specific SVG icons (Globe, AppWindow, Volume2, Camera, Layers), human-readable titles, browser badges, and collapsible execution details.
5. **Native Desktop Executable (`AegisAI.exe`) & Windows Startup Integration**:
   - Compiled `scripts/launcher.cs` using Windows native Roslyn `csc.exe` into a 13.3 KB `winexe` binary with embedded shield icon. Runs completely detached without any console window.
   - Single-instance enforcement via Windows Mutex (`Global\AegisAI_Desktop_Mutex_2026`).
   - Integrated `WindowsStartupManager` using native `winreg` on `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`.
   - Right-click tray menu toggle ("Start with Windows") and CLI flags (`--install-startup`, `--remove-startup`, `--background`).
6. **Testing & QA Verification**:
   - All 58 backend tests passing in `backend/tests` (10/10 in `test_arabic_voice_tools.py`).
   - 0 Flake8 lint warnings across `backend/`, `scripts/`, and `aegis.py`.
   - Built distribution package with SHA-256 validation.
