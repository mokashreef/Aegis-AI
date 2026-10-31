# PR: Phase 12 - 1-Click Offline Model Download Wizard with Live Byte Progress

## Summary
- **Issue**: Resolves [Issue #12](https://github.com/mokashreef/Aegis-AI/issues/12)
- **Branch**: `feat/model-download-wizard` -> `main`
- **Labels**: `ai-runtime`, `ollama`, `wizard`, `frontend`, `p1`

## Motivation & Solution
This PR transforms the initial setup experience for users who run Aegis AI without pre-downloaded local models.
Rather than displaying a simple warning or relying indefinitely on cloud fallbacks, Aegis AI now guides users through an intuitive 1-click Model Download Wizard.

## Changes
1. **Interactive Model Wizard Grid (`ModelSetupBanner.tsx`)**:
   - Offers choice of Qwen 2.5 (1.5B), Llama 3.2 (1B), and Llama 3.2 (3B) with hardware recommendations.
   - Dynamic selection highlight and 1-click download activation.
2. **Streaming Byte Telemetry**:
   - Real-time download progress formatting (`MB / GB`).
   - Detailed phase status display ("pulling manifest", "downloading", "verifying sha256").
3. **Smart Environment Detection**:
   - Direct download link to `https://ollama.com/download` if Ollama is missing from host.
   - Background daemon launch button if Ollama is installed but not running.
4. **Backend Streaming Test Suite (`test_ai_runtime.py`)**:
   - Added unit tests for `OllamaProvider.pull_model_stream` chunk decoding.
   - Added integration test for SSE streaming endpoint `/api/models/pull`.
5. **Quality Assurance**:
   - Production Vite frontend compiled in 9.42s.
   - 48 tests passing in 12.05s.
   - 0 flake8 warnings.
