# PR: Native Desktop Executable (.exe), Windows Startup Daemon, Compound Arabic Voice NLP & Modern UI Overhaul

- **Branch**: `feat/native-app-arabic-nlp-ui-startup`
- **Base**: `main`
- **Issue Reference**: Resolves Issue #14
- **Status**: Ready for Merge

---

## 1. Summary of Changes

This pull request addresses user feedback regarding the desktop experience, voice command routing, window layering, and visual design:

### A. Native Windows Desktop Executable (`AegisAI.exe`)
- Replaces command prompt and batch scripts with a native Windows `winexe` binary compiled via Roslyn (`scripts/launcher.cs` $\rightarrow$ `AegisAI.exe`).
- Features embedded official shield icon (`assets/icon.ico`).
- Single-instance Mutex (`Global\AegisAI_Desktop_Mutex_2026`) prevents duplicate processes.
- Runs completely detached from any console window using `pythonw.exe` inside the isolated virtual environment.

### B. Windows Startup Auto-Launch Daemon
- Created `WindowsStartupManager` using native Windows Registry (`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`).
- Added right-click system tray menu item: `"Start with Windows"` with dynamic checkmark.
- Exposed REST API endpoints: `GET /api/desktop/startup` and `POST /api/desktop/startup/toggle`.
- Added CLI switches: `AegisAI.exe --install-startup`, `--remove-startup`, and `--background`.

### C. Spoken Arabic Phonetic & Compound Intent Routing
- Spoken domain normalization (`normalize_spoken_arabic_text`): converts spoken phonetic domains ("دوت نت" $\rightarrow$ `.net`, "دوت كوم" $\rightarrow$ `.com`, "دوت اورج" $\rightarrow$ `.org`, etc.).
- Compound sentence parsing: extracts browser and destination from complex Arabic expressions like `"كروم و افتح موقع كود التطور دوت نت"`.
- Defensive fallback in `LaunchAppTool`: Automatically catches any URL/domain commands that fall into application launch and redirects them seamlessly to `OpenUrlTool`.

### D. Natural Window Focus & Z-Order (No More Always-On-Top Lock)
- Window defaults to standard OS Z-order (`_is_on_top = False`, `isPinned = false`).
- Clicking other apps (Chrome, Codex, VSCode) naturally brings them to the front and puts Aegis behind them.
- Users can still toggle the Pin button in the header if they want Aegis to stay permanently on top.

### E. Spacious & Modern UI Overhaul
- Window dimensions expanded from 760x620 to 780x640.
- Completely redesigned `ActionCard.tsx` with tool-specific SVG icons (Globe, AppWindow, Volume2, Camera, Layers), human-readable titles, browser badges, and collapsible execution details.
- Faster STT & VAD chunking (900ms trailing silence, `condition_on_previous_text=False`).

---

## 2. Verification & Test Evidence

- **Unit & Integration Tests**: 58/58 passed in 38.37s.
  - `backend/tests/test_arabic_voice_tools.py` passed 10/10.
- **Linting**: Flake8 passed with 0 warnings across all files.
- **Packaging**: Automated distribution build succeeded:
  - Archive: `Aegis-AI-v0.2.0-alpha-Windows-x64-Portable.zip` (5.26 MB)
  - SHA-256: `4d04d67533a0354fb6ce8208a62fcca08de2975af71f1482c0b1c080fa60bd00`
