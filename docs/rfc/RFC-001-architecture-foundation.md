# RFC-001: Architectural Foundation of Aegis AI

- **Author**: Lead Architect
- **Status**: ACCEPTED
- **Date**: 2026-10-31
- **Target Subsystems**: All (Core Daemon, Frontend HUD, Desktop Shell, AI Runtime, Tool Engine)

---

## 1. Context and Problem Statement

Desktop AI assistants frequently suffer from three critical architectural flaws:
1. **Mandatory Cloud & Subscription Lock-In**: Users are forced to provide paid OpenAI, Anthropic, or AWS keys, preventing widespread open-source adoption and exposing confidential desktop data to third parties.
2. **Heavyweight Resource Footprint**: Bloated Electron wrappers consume gigabytes of RAM while idling in the Windows system tray.
3. **Superficial OS Integration**: Most assistants are web wrappers that cannot interact meaningfully with native Windows windows, processes, clipboard, or local files.

Aegis AI resolves these issues by combining a lightweight **Tauri (Rust)** desktop shell, a decoupled **Python Core Engine** for local AI and automation, and a high-performance **React / TypeScript** overlay interface.

---

## 2. Architectural Pillars

### Pillar I: Zero Mandatory API Keys
Aegis AI treats local hardware as the primary execution target. The AI Runtime evaluates available models via local `ollama` instances first. When local hardware is constrained, the runtime routes requests through free, rate-limit-friendly open inference endpoints (e.g. Pollinations AI, open HuggingFace inference, Groq free tier).

### Pillar II: Separation of Concerns (Hexagonal / Ports-and-Adapters)
```
       +--------------------------------------------+
       |     Tauri Shell (Rust + Win32 Hook)        |
       |  - Global Hotkeys: Alt+Space, Win+Space    |
       |  - Transparent Frameless Window Overlay    |
       |  - System Tray Integration                 |
       +---------------------+----------------------+
                             |
                             v
       +--------------------------------------------+
       |   Frontend HUD (React 18 + Vite + TS)      |
       |  - Streaming Markdown renderer             |
       |  - Voice Audio Visualizer                  |
       |  - Tool Execution Status Cards             |
       +---------------------+----------------------+
                             | WebSocket / REST
                             v
       +--------------------------------------------+
       |   Aegis Core Daemon (Python 3.11 / FastAPI)|
       |  +---------------------------------------+ |
       |  | Orchestrator & ReAct Planner Loop     | |
       |  +---------------------------------------+ |
       |  | AI Runtime Multi-Tier Fallback Router | |
       |  +---------------------------------------+ |
       |  | Windows Automation & Process Controller |
       |  +---------------------------------------+ |
       |  | SQLite Persistent Memory & Session Log| |
       |  +---------------------------------------+ |
       |  | Voice Pipeline (Faster-Whisper/Piper) | |
       |  +---------------------------------------+ |
       +--------------------------------------------+
```

### Pillar III: Asynchronous Event-Driven Communication
Communication between the Frontend HUD and the Python Core Daemon uses persistent WebSockets for bidirectional real-time streaming:
- **Token streaming**: Sub-word token streaming from local LLMs.
- **Tool execution telemetry**: Instant progress notifications when the agent performs multi-step automation.
- **Audio packet streaming**: Streaming PCM audio between the user microphone, Whisper, and Piper.

---

## 3. Security and Permission Boundaries

To ensure desktop safety, all tools registered with Aegis AI carry a risk classification:
- `READ_ONLY`: File inspection, process listing, time/date checking, web searching. Can be executed autonomously.
- `MUTATING_SAFE`: Clipboard copy, launching whitelisted applications, navigating active browser tabs.
- `RESTRICTED_CONFIRM`: File deletion, executing arbitrary shell scripts, modifying Windows registry, terminating running processes. Requires explicit user confirmation via the HUD.

---

## 4. Alternative Solutions Considered

| Approach | Rejected Reason |
| :--- | :--- |
| **Pure Electron** | High memory footprint (~400MB idle vs ~40MB Tauri), slower cold starts, bundled Chromium duplication. |
| **Pure Python GUI (PyQt/CustomTkinter)** | Inadequate modern glassmorphism UI fidelity, poor multi-monitor DPI scaling, harder to skin than web standards. |
| **Pure Rust AI Engine** | Python has vastly superior ecosystems for local AI, PyTorch, Whisper, Piper, and Playwright automation. Decoupling Rust (Shell) and Python (Brain) provides the optimal balance. |

---

## 5. Conclusion & Implementation Plan
This RFC serves as the binding blueprint for Milestone 1 through Milestone 4.
Implementation begins with the Python Core Daemon, local fallback engine, SQLite persistence, and React HUD.
