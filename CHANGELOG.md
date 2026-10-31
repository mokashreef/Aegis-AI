# Changelog

All notable changes to the **Aegis AI** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added - Phase 1: Real Windows Presence (MVP Recovery)
- **Native Windows Global Hotkey (`Alt + Space`)**: Implemented via Win32 low-level keyboard hook (`WH_KEYBOARD_LL`), ensuring system-wide capture regardless of which desktop application is focused and bypassing `ERROR_HOTKEY_ALREADY_REGISTERED`.
- **Frameless Always-On-Top Native Overlay**: Pinned WebView2 desktop window with glassmorphism, multi-monitor active cursor centering, and spotlight alignment.
- **Instant Dismissal**: `ESC` key global listener and top-right dismiss action that hides the overlay in < 15ms.
- **Zero Browser Dependency**: Packaged React HUD (`apps/desktop-ui/dist`) directly into FastAPI static mount; eliminated the need for `localhost:5173` or `npm run dev`.
- **Single Desktop Entrypoint**: Added `aegis.py` and `scripts/run_desktop.ps1` for one-click startup.

---

## [0.1.0-alpha] - 2026-10-31

### Initial Release
- Project repository initialization and architecture bootstrap.
- Zero-API-key architecture specification and implementation.
- Milestone 1: MVP Core Assistant foundations.

