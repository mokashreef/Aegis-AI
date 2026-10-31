# System Overview & Architecture Summary

Aegis AI is an open-source, local-first Windows AI companion designed to provide seamless desktop intelligence, natural voice interaction, operating system automation, and autonomous task reasoning with **Zero Mandatory API Keys**.

---

## High-Level Topology

```
+-------------------------------------------------------------------+
|                           WINDOWS HOST                            |
|                                                                   |
|   +-----------------------------------------------------------+   |
|   |                 Tauri Shell (Rust v2)                     |   |
|   |   - Global Hotkeys (Alt+Space / Win+Space)                |   |
|   |   - System Tray Icon & Notifications                      |   |
|   |   - Multi-monitor Coordinate Positioning                  |   |
|   +-----------------------------+-----------------------------+   |
|                                 |                                 |
|                                 v                                 |
|   +-----------------------------------------------------------+   |
|   |            Frontend HUD (React 18 + TypeScript)           |   |
|   |   - Frameless Transparent Glassmorphic Window             |   |
|   |   - Real-Time Token Streaming & Voice Waveform Visualizer |   |
|   |   - Interactive Action Confirmation Cards                 |   |
|   +-----------------------------+-----------------------------+   |
|                                 | WebSocket & REST                |
|                                 v                                 |
|   +-----------------------------------------------------------+   |
|   |               Aegis Core Daemon (Python 3.11)             |   |
|   |   +-----------------------------------------------------+ |   |
|   |   | AI Runtime: Ollama First -> Pollinations Fallback   | |   |
|   |   +-----------------------------------------------------+ |   |
|   |   | ReAct Reasoning Loop & Multi-Step Planner           | |   |
|   |   +-----------------------------------------------------+ |   |
|   |   | Windows Automation: Process / Window / Clipboard    | |   |
|   |   +-----------------------------------------------------+ |   |
|   |   | SQLite Memory (WAL Mode) & Vector Search Storage    | |   |
|   |   +-----------------------------------------------------+ |   |
|   |   | Voice Pipeline: Faster-Whisper STT & Piper TTS      | |   |
|   |   +-----------------------------------------------------+ |   |
|   |   | Dynamic Plugin Registry with Safety Guardrails      | |   |
|   |   +-----------------------------------------------------+ |   |
|   +-----------------------------------------------------------+   |
+-------------------------------------------------------------------+
```

---

## Core Tenets

1. **Local First**: Prioritizes running locally through Ollama, faster-whisper, and piper.
2. **Zero API Key Requirement**: Operates out of the box with zero subscriptions, accounts, or paid credentials.
3. **Graceful Fallback**: Automatically cascades to free anonymous endpoints if local models are offline.
4. **Safety by Default**: Destructive operations (process termination, file manipulation) require explicit visual confirmation.
