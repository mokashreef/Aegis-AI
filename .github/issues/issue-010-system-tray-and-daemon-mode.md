# Issue #10: Native System Tray Icon, Background Daemon Mode & Minimization

- **Labels**: `desktop`, `system-tray`, `daemon`, `ux`, `p1`
- **Milestone**: MVP Desktop Experience
- **Status**: CLOSED (Resolved with Empirical Proof)
- **Branch**: `feat/system-tray-daemon`

## Problem Analysis
Previously, closing the PyWebView desktop window or terminating the window session caused the entire application to exit. This broke the ambient companion experience where Aegis AI is expected to run silently in the background, ready to be summoned instantly via `Alt+Space` or wake-word detection ("Hey Aegis").

## Target Deliverables & Verification
1. **Native Windows System Tray Icon (`pystray`)**:
   - Implemented `TrayIconManager` in `backend/aegis_core/desktop/tray.py`.
   - Runs detached on an independent daemon thread without blocking FastAPI or PyWebView.
   - Generates and bundles high-definition multi-resolution icons (`assets/icon.ico`, `assets/icon.png`).
2. **Context Menu Actions**:
   - "Show Aegis AI (Alt+Space)" (default double-click handler)
   - "Wake Word: Hey Aegis" (live dynamic state indicator and toggle)
   - "Open Companion Web HUD" (launches browser directly to local endpoint)
   - "Exit Aegis AI" (coordinates clean shutdown across tray, hotkeys, and server)
3. **Window Minimization / Hide-on-Close**:
   - Subscribed to PyWebView `closing` event in `window.py`.
   - Automatically intercepts user close/Alt+F4 actions, calls `overlay_manager.hide()`, and cancels destruction (`returns False`) unless explicitly quitting via tray.
4. **Integration & Packaging**:
   - Wired into `aegis.py` application entrypoint.
   - Updated `scripts/build_distribution.py` to bundle `assets/` into portable releases.
   - Updated `installer/aegis_setup.iss` with `SetupIconFile` and shortcut iconography.
5. **Testing & Quality**:
   - 5 dedicated unit tests in `backend/tests/test_tray.py`.
   - Total test suite: 46 passed in 15.66s.
   - Flake8: 0 warnings.
