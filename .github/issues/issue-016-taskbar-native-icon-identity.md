# Issue #16: Native Windows Taskbar Icon & Application Identity (Replacing Generic Python Icon with Official Shield Asset)

- **Labels**: `ui`, `desktop`, `windows`, `branding`, `taskbar`, `p1`
- **Milestone**: MVP Usability & Polish
- **Status**: CLOSED

## Completed Deliverables

1. **Process AppUserModelID Registration (`aegis.py`, `window.py`)**:
   - Set `ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("AegisAI.Desktop.Companion.2026")` at the entry point of `aegis.py` and `window.py`.
   - Windows Shell Taskbar immediately decouples the running application from `pythonw.exe` and groups all Aegis AI windows under its own dedicated identity.
2. **PyWebView WinForms Icon Binding (`window.py`)**:
   - Passed `icon=str(Path(settings.base_dir) / "assets" / "icon.ico")` to `webview.start(...)`.
   - PyWebView's Windows WinForms backend assigns `self.Icon = Icon(_state['icon'])` instead of falling back to extracting the Python document icon from `sys.executable`.
3. **Win32 `WM_SETICON` Native Dispatch (`window.py`)**:
   - Added `_apply_native_window_icon()` on `_on_shown`: loads `assets/icon.ico` using `LoadImageW` and sends `WM_SETICON` messages for both `ICON_BIG` (32x32 Alt+Tab) and `ICON_SMALL` (16x16 Taskbar & Titlebar) directly to the Win32 HWND.
4. **C# Native Launcher Alignment (`scripts/launcher.cs`, `AegisAI.exe`)**:
   - Aligned `AegisAI.exe` with the same `AppUserModelId` (`AegisAI.Desktop.Companion.2026`) via `shell32.dll`.
   - Recompiled `AegisAI.exe` with embedded shield icon via `csc.exe /win32icon:assets\icon.ico`.
5. **Quality Assurance & Verification**:
   - 64/64 unit & integration tests passing in `backend/tests`.
   - 0 Flake8 lint warnings across all Python code.
   - Built updated portable distribution archive with SHA-256 validation.
- **Branch**: `fix/taskbar-icon-app-identity`

## Problem Analysis

User reported and provided screenshot evidence:
When running Aegis AI on Windows, the Windows Taskbar displays the generic Python document script icon (`.py` file with Python snake logo on a white sheet) instead of the official Aegis AI application shield icon (`assets/icon.ico`).

### Root Causes
1. **Windows AppUserModelID Unset in Python Process**:
   Windows Shell groups windows on the Taskbar according to the Application User Model ID (AUMID). Because `pythonw.exe` didn't explicitly register an AUMID via `shell32.SetCurrentProcessExplicitAppUserModelID`, Windows Shell associated the window with `pythonw.exe`'s file association, rendering the generic Python script icon.
2. **Missing `icon` parameter in PyWebView**:
   In `backend/aegis_core/desktop/window.py`, `webview.start(debug=settings.debug)` was called without `icon=...`. In PyWebView's Windows backend (`winforms.py`), when `_state['icon']` is None, it extracts the icon from `sys.executable` (`pythonw.exe`), explicitly assigning the Python icon to the Form.
3. **Missing Win32 `WM_SETICON` on HWND**:
   The native window handle was not explicitly updated with Win32 `WM_SETICON` (`ICON_BIG` for Alt+Tab and `ICON_SMALL` for Taskbar and Titlebar).
4. **Launcher `launcher.cs` App ID alignment**:
   `AegisAI.exe` and the spawned Python runtime must share the exact same `AppUserModelID` (`AegisAI.Desktop.Companion.2026`) so Windows Taskbar pins and buttons map directly to `AegisAI.exe` and its embedded shield icon.

## Implementation Plan

1. **Process AUMID Registration (`aegis.py`, `window.py`)**:
   Set `ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("AegisAI.Desktop.Companion.2026")` at the entry point before any window or thread initialization.
2. **Pass Icon Asset to `webview.start` (`window.py`)**:
   Pass `icon=str(Path(settings.base_dir) / "assets" / "icon.ico")` to `webview.start(...)`, allowing PyWebView WinForms to set `self.Icon = Icon(icon_path)`.
3. **Win32 Native `WM_SETICON` Dispatch (`window.py`)**:
   In `_on_shown`, load `assets/icon.ico` via `LoadImageW` and dispatch `WM_SETICON` (`ICON_BIG` & `ICON_SMALL`) to the native HWND.
4. **Update & Recompile C# Launcher (`scripts/launcher.cs`, `AegisAI.exe`)**:
   Set `SetCurrentProcessExplicitAppUserModelID` in `launcher.cs` and recompile `AegisAI.exe` with `/win32icon:assets\icon.ico`.
5. **Rebuild Distribution Package & Verification**:
   Rebuild `AegisAI.exe` and distribution ZIP, run test suite, and ensure 0 flake8 warnings.
