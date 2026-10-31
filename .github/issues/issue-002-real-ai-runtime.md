# Issue #2: Real AI Runtime & Model Bootstrapper

- **Labels**: `enhancement`, `ai-runtime`, `ollama`, `mvp`, `p0`
- **Milestone**: MVP Recovery (Phase 2)
- **Status**: IN PROGRESS
- **Branch**: `feat/phase2-real-ai-runtime`

## Problem Statement
Aegis AI's runtime was fragile:
1. `is_available()` reported true even when Ollama had zero models downloaded, causing unhandled 404 errors.
2. Pollinations AI was used as primary fallback, hitting severe 45-second rate limits.
3. Users had no feedback on why the AI wasn't responding, no tokens/sec telemetry, and no ability to install recommended local models with one click.

## Scope & Acceptance Criteria
1. **Ollama Deep Probe**:
   - Detect server online/offline state.
   - Detect installed model count and active model existence.
   - If server is running but has no models, mark state as `NEEDS_MODEL` rather than `ONLINE`.
2. **One-Click Model Bootstrapper**:
   - API endpoint `/api/models/pull` that pulls recommended small local models (`qwen2.5:1.5b` or `llama3.2:1b`) directly from Ollama registry.
   - Streams pull progress (layer download, bytes completed, percent) over WebSocket / Server-Sent Events.
3. **Runtime Dashboard & Telemetry in HUD**:
   - Live banner in HUD when no model is installed with a single "Install Qwen 2.5 1.5B (1GB)" button.
   - Telemetry displays active provider, tokens/second measurement, active model, and failure reasons.
4. **De-prioritize Pollinations**:
   - Pollinations is isolated as a secondary fallback only, with clear rate-limit warning.
