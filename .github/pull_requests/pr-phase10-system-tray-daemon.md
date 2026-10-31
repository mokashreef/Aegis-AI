# PR: Phase 10 - Native Windows System Tray Companion & Background Daemon Mode

## Summary
- **Issue**: Resolves [Issue #10](https://github.com/mokashreef/Aegis-AI/issues/10)
- **Branch**: `feat/system-tray-daemon` -> `main`
- **Labels**: `desktop`, `system-tray`, `daemon`, `ux`, `p1`

## Motivation & Solution
Prior to this PR, closing the PyWebView desktop window terminated the entire process, requiring manual relaunch every time.
This PR transforms Aegis AI into a persistent Windows desktop companion that resides in the notification area (System Tray).

## Changes
1. **Tray Icon Manager (`backend/aegis_core/desktop/tray.py`)**:
   - Manages the notification area icon using `pystray`.
   - Runs detached on a background thread.
   - Generates and persists `assets/icon.png` and `assets/icon.ico` (multi-res 16/32/48/64px).
2. **Context Menu**:
   - Double-click or select "Show Aegis AI (Alt+Space)" to summon overlay.
   - "Wake Word: Hey Aegis" live checkmark and toggle.
   - "Open Companion Web HUD" to open browser directly.
   - "Exit Aegis AI" for clean shutdown.
3. **Hide-on-Close Interception (`backend/aegis_core/desktop/window.py`)**:
   - Subscribes to `closing` event.
   - Cancels window destruction (`return False`) and calls `hide()` to preserve background daemon operation unless quitting.
4. **App Entrypoint & Packaging**:
   - Integrated into `aegis.py` lifecycle.
   - Staged in `scripts/build_distribution.py` and `installer/aegis_setup.iss`.
5. **Quality Assurance**:
   - 46 unit and integration tests passing (`pytest backend/tests -v`).
   - 0 flake8 warnings.
