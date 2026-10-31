# Pull Request: Phase 2 — Real AI Runtime & Model Bootstrapper (MVP Recovery)

## Summary
Solves the empty Ollama model crash, introduces deep server probing, adds an in-app one-click model bootstrapper for `qwen2.5:1.5b`, isolates Pollinations rate-limiting to emergency-only mode, and surfaces live tokens/second telemetry.

## Changes Included
- **Ollama Deep Probing & Crash Prevention** (`aegis_core.ai_runtime.ollama_provider`):
  - Added `probe_health()` detecting binary presence, server status, model count, and status reason.
  - `is_available()` strictly returns `False` if zero models are installed, preventing unhandled 404 crashes.
  - Automatically identifies local Windows `ollama.exe` and offers background launch via `/api/ollama/start`.
- **One-Click Model Bootstrapper** (`backend/aegis_core/api/routes.py` & `apps/desktop-ui/src/components/ModelSetupBanner.tsx`):
  - Added `/api/models/pull` streaming NDJSON pull progress from Ollama library.
  - Added HUD setup banner with real-time percentage progress bar to install `qwen2.5:1.5b` (~986MB).
- **Live Speed Telemetry** (`aegis_core.ai_runtime.router`):
  - Measures generation throughput and emits `tokens_per_second` displayed directly in the HUD header (`⚡ XX.X t/s`).
- **Emergency Fallback Isolation**:
  - Clear rate-limit notice attached to Pollinations; prevents silent blocking.

## Testing & Quality Verification
- 17/17 unit & integration tests passing (`pytest backend/tests`).
- `flake8 backend` passing with 0 warnings.
- Frontend bundle built with 0 TypeScript compiler errors.
