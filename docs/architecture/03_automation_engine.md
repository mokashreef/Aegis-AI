# Windows Desktop Automation Engine Specification

The Windows Desktop Automation Engine provides Aegis AI with direct, low-latency, safe manipulation of the Windows operating system.

---

## 1. Capabilities Matrix

| Subsystem | Underlying API / Library | Operational Scope | Safety Level |
| :--- | :--- | :--- | :--- |
| **Process Manager** | `psutil` + Windows `kernel32.dll` / `CreateProcessW` | Enumerate processes, launch desktop apps, terminate processes | `MUTATING_SAFE` / `RESTRICTED_CONFIRM` |
| **Window Controller** | `user32.dll` (`EnumWindows`, `SetForegroundWindow`, `ShowWindow`) | Find window handles, focus, minimize, maximize, restore, tile | `MUTATING_SAFE` |
| **Clipboard Controller** | `user32.dll` (`OpenClipboard`, `GetClipboardData`, `SetClipboardData`) | Read text/HTML clipboard formats, write responses or snippets | `MUTATING_SAFE` |
| **Keyboard / Mouse Simulator** | `SendInput` via `ctypes` / `pyautogui` | Emulate user keystrokes, shortcuts, mouse clicks | `MUTATING_SAFE` |
| **Browser Controller** | Playwright (`chromium`) | Headless browser navigation, DOM inspection, form input | `MUTATING_SAFE` |

---

## 2. Safety Interceptors & Human-in-the-Loop Confirmation

Destructive operations cannot be executed autonomously by the AI planner without passing through the `ActionGate`:

1. When the agent decides to invoke a tool flagged with `RiskLevel.RESTRICTED_CONFIRM`:
   - The tool execution pauses.
   - A structured confirmation payload is emitted over WebSocket to the Frontend HUD.
   - The user is shown an **Action Confirmation Card** describing the target application, PID, or path.
   - The action is only dispatched upon receiving an explicit `user_confirmed` response.
2. File deletions route to the Windows Recycle Bin (via `shell32.SHFileOperationW`) rather than permanent unlinking (`os.remove`), preventing accidental data loss.
