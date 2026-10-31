# Pull Request: Useful Automation (Fuzzy App Matcher, Intent Classification & Window Management)

## Title
`feat(automation): implement fuzzy app discovery, natural language intent routing, and Win32 window management (Phase 4)`

## Summary
Eliminates brittle prefix string matching (`text.startswith("open ")`) and implements production-grade Windows desktop automation:
1. **Fuzzy Application Discovery & Matcher**:
   - `AppFinder` indexes Start Menu shortcuts, Windows Registry `App Paths`, and system tools.
   - Handles natural conversational phrasing: "open chrome", "launch google chrome", "can you start notepad please", "calc", "vscode".
2. **Natural Language Intent Router**:
   - `IntentRouter` classifies user intent in microseconds with zero cloud dependency.
   - Dispatches to app control, window snapping, desktop minimization, system telemetry, and clipboard queries, falling back gracefully to LLM conversation.
3. **Win32 Window Management**:
   - Added `minimize_all` (native Win+D simulation).
   - Added monitor work-area aware `snap_window` (left, right, maximize).
   - Added `focus_window_by_title` to bring running applications to foreground.
4. **Resilient Agent Feedback**:
   - Synthesizes immediate natural confirmation even if local AI model is offline.

## Verification
- `pytest backend/tests -v` -> 27/27 tests passing.
- `flake8 backend` -> 0 warnings.

