# Pull Request: Daily Value Features (Volume, Brightness, Window Snapping, Screen Capture & Quick Notes)

## Title
`feat(desktop): implement Windows volume, brightness, window snapping, screen capture, and daily notes (Phase 5)`

## Summary
Delivers 5 high-frequency daily value capabilities that make Aegis AI immediately useful as an everyday Windows companion with zero external cloud dependencies:
1. **System Audio Volume Control**:
   - Master volume query, percentage adjustment (0-100%), mute/unmute, and relative step tuning via Windows CoreAudio API (`pycaw`).
2. **Display Brightness Control**:
   - Monitor brightness adjustment and status polling using native Windows WMI (`WmiMonitorBrightnessMethods`).
3. **Multi-Monitor Window Snapping**:
   - Win32 API window tiling (`snap_left`, `snap_right`, `maximize`, `restore`) respecting taskbar work area boundaries.
4. **Desktop Screen Capture**:
   - Captures screenshots, stores local PNGs in cache, and returns base64 data URLs for multimodal agent reasoning.
5. **Quick Daily Notes**:
   - Appends timestamped notes to local markdown daily logs (`data/notes/YYYY-MM-DD.md`) with search capabilities.
6. **Natural Language Routing**:
   - Natural language commands ("set volume to 60%", "dim screen", "take a screenshot", "note down...") execute instantly.

## Verification
- `pytest backend/tests -v` -> 33/33 tests passing.
- `flake8 backend` -> 0 warnings.
- `npm run build` in `apps/desktop-ui` -> 0 errors.
