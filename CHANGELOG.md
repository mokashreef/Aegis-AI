# Changelog

All notable changes to the **Aegis AI** project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- **Core Architecture Foundation**: Modular separation between Tauri Desktop Shell, React/TypeScript HUD, and Python Core Daemon.
- **Autonomous Zero-Cost AI Runtime Engine**: Multi-tier LLM provider pipeline with Ollama as primary local runtime and zero-cost fallback integrations (Pollinations AI, HuggingFace Inference API, Groq Free Tier).
- **Windows Desktop Automation Framework**: Process manager, application launcher, active window tracker, clipboard controller, and UI automation primitives via `ctypes` and Windows Win32 APIs.
- **Local Conversational Memory Engine**: SQLite storage engine with conversation persistence, session isolation, and contextual memory recall.
- **Voice Pipeline Architecture**: Faster-Whisper local speech-to-text integration and Piper neural text-to-speech engine.
- **Dynamic Plugin Subsystem**: Modular tool registration protocol enabling extensible user automation scripts and plugins.
- **Modern HUD Overlay Interface**: React 18 + Vite + TypeScript desktop companion UI designed for transparent floating overlay and system tray orchestration.
- **Comprehensive Project Governance**: Complete GitHub workflow, issue templates, PR guidelines, RFC framework, security policy, and 12-month engineering roadmap.

---

## [0.1.0-alpha] - 2026-10-31

### Initial Release
- Project repository initialization and architecture bootstrap.
- Zero-API-key architecture specification and implementation.
- Milestone 1: MVP Core Assistant foundations.
