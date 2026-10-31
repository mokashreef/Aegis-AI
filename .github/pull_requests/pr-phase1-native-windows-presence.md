# Pull Request: Phase 1 — Native Windows Presence (MVP Recovery)

## Summary
Transforms Aegis AI from a browser-dependent web chat into a real native Windows desktop companion summoned by `Alt + Space`.

## Changes Included
- **Native Global Hotkey (`Alt + Space`)**: Implemented using Win32 low-level keyboard hook (`WH_KEYBOARD_LL`) in `aegis_core.desktop.hotkey`. Operates across all active Windows applications and avoids `ERROR_HOTKEY_ALREADY_REGISTERED`.
- **Native Frameless Overlay Window**: Added `aegis_core.desktop.window` using `pywebview` (Microsoft WebView2 backend). Pinned `AlwaysOnTop`, frameless, with dynamic multi-monitor coordinate detection centering the HUD on the active screen where the user's cursor resides.
- **Eliminated Browser Tab Dependency**: Mounted production-compiled React HUD (`apps/desktop-ui/dist`) directly into FastAPI at `/`. User does not need `localhost:5173`, `npm run dev`, or any browser tabs.
- **Dismissal Controls**: `ESC` key press or close button dismisses the overlay window in < 15ms.
- **Entrypoint**: Added `aegis.py` and `scripts/run_desktop.ps1` for one-click startup.

## Testing & Quality Verification
- 15/15 unit tests passing (`pytest backend/tests`).
- `flake8` linting passing with 0 warnings.
- Frontend production bundle built with 0 TypeScript compiler errors.
- Active monitor coordinate detection and Win32 hook installation verified on Windows 10/11 host.

