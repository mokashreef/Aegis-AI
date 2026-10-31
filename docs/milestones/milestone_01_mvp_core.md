# Milestone 1: MVP Core Assistant & Windows Companion

## Overview
- **Phase**: MVP / Foundation
- **Target Timeline**: Months 1–3 (Q1)
- **Status**: IN PROGRESS
- **Goal**: Ship the functional, zero-paid-API-key Windows companion supporting hotkey summoning, local/free AI chat, voice synthesis, basic desktop controls, and persistent memory.

---

## Detailed Deliverables Breakdown

| Work Item ID | Deliverable | Scope | Status | Acceptance Criteria |
| :--- | :--- | :--- | :--- | :--- |
| **M1-CORE-01** | Python Core Daemon (`aegis-core`) | FastAPI + WebSocket asynchronous event bus | Completed | Daemon boots in < 500ms, exposes health and chat endpoints, handles graceful shutdown. |
| **M1-CORE-02** | Zero-Cost AI Runtime Engine | Ollama primary provider + Pollinations/HF fallbacks | Completed | Automatic detection of local models; seamless failover without breaking client stream. |
| **M1-CORE-03** | Local Memory & Database Engine | SQLite persistence for sessions and messages | Completed | Messages, tokens, and metadata persisted locally with foreign keys and indexes. |
| **M1-UI-01** | React/TS Companion HUD | Sleek overlay interface with Lucide icons | Completed | Minimalist floating HUD, glassmorphism UI, keyboard input navigation. |
| **M1-UI-02** | Tauri Desktop Container | Rust desktop wrapper with global hotkeys | Completed | Configured for multi-window overlay, system tray icon, and background persistence. |
| **M1-AUTO-01** | Basic Desktop Automation Tools | Process launch, termination, clipboard control | Completed | Can launch Notepad, inspect processes, read/write clipboard reliably via Win32. |
| **M1-VOICE-01** | Offline Speech Engine Interface | Faster-Whisper and Piper TTS bindings | Completed | Clean abstractions and streaming playback for local speech synthesis. |
| **M1-DOC-01** | Open Source Governance & CI/CD | Full GitHub templates, actions, architecture docs | Completed | Clean CI workflow, flake8 passing, TypeScript compiling, security policy defined. |

---

## Technical Specifications & Verification

### 1. Zero API Key Requirement
The system must successfully answer user queries immediately after installation without prompting for a credit card, OpenAI key, or cloud registration.

### 2. Failure Isolation
If Ollama is not installed or temporarily offline:
1. The engine checks local Ollama endpoint (`http://localhost:11434`).
2. If unreachable, the engine gracefully transitions to Pollinations AI (`https://text.pollinations.ai/`) or HuggingFace free inference.
3. The user is presented with a non-intrusive warning indicating offline fallback mode.

