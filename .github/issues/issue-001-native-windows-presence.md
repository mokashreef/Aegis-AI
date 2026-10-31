# Issue #1: Native Windows Presence (Alt+Space Global Hotkey & Desktop Overlay)

- **Labels**: `enhancement`, `mvp`, `desktop`, `p0`
- **Milestone**: MVP Recovery (Phase 1)
- **Status**: IN PROGRESS
- **Branch**: `feat/phase1-native-windows-presence`

## Problem Statement
Aegis AI currently behaves like a web chatbot running on `http://localhost:5173`. A user must manually launch npm and open a browser tab. `Alt + Space` is intercepted by the browser or active Windows application rather than summoning Aegis.

## Scope & Acceptance Criteria
1. **Native Global Hotkey (`RegisterHotKey`)**:
   - Register system-wide `Alt + Space` hook via Windows Win32 API.
   - Works regardless of which desktop app currently has focus.
   - Configurable fallback hotkey.
2. **Native Overlay Window**:
   - Borderless, frameless native window.
   - Pinned `AlwaysOnTop` (`HWND_TOPMOST`).
   - Centered on the active screen / monitor.
   - `ESC` key press hides the window immediately.
   - Loss of focus / clicking outside hides the window.
3. **Zero Browser Dependency**:
   - Compiled React HUD (`apps/desktop-ui/dist`) served directly by the backend and embedded into native Windows WebView2.
   - User launches `python -m aegis_core.main` (or `aegis.py`) and Aegis is active in the background ready for `Alt+Space`.

