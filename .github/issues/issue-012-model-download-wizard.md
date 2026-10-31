# Issue #12: 1-Click Offline Model Download Wizard with Live Byte Progress

- **Labels**: `ai-runtime`, `ollama`, `wizard`, `frontend`, `p1`
- **Milestone**: MVP Model Matrix
- **Status**: CLOSED (Resolved with Empirical Proof)
- **Branch**: `feat/model-download-wizard`

## Problem Analysis
When a user launches Aegis AI on a computer where Ollama has zero models installed, the system falls back to external zero-cost providers. To fulfill the core local-first, zero-cloud promise of Aegis AI, the desktop overlay must provide a friction-free, 1-click Model Download Wizard that guides the user through installing optimal local SLMs (Small Language Models) with full live telemetry.

## Delivered Solution
1. **Multi-Model Wizard Grid (`apps/desktop-ui/src/components/ModelSetupBanner.tsx`)**:
   - Offers lightweight models suited for standard consumer hardware:
     - **Qwen 2.5 (1.5B)** (986 MB, fast CPU inference, 8-16GB RAM) - Tagged "Recommended for CPU".
     - **Llama 3.2 (1B)** (1.3 GB, lightweight Meta architecture).
     - **Llama 3.2 (3B)** (2.0 GB, high accuracy for modern GPUs / 16GB+ RAM).
   - Interactive card selector with highlighted active selection ring.
2. **Real-Time Byte Progress Telemetry**:
   - Live formatted byte download counters (e.g. `450.2 MB / 986.0 MB`).
   - Percentage indicator and glowing animated gradient progress bar (`Math.max(2, percent)`).
   - Stage status updates (`"pulling manifest"`, `"downloading"`, `"verifying sha256"`, `"success"`).
3. **Smart Environment Diagnostics**:
   - Uninstalled State: Clear guidance with external link to `https://ollama.com/download`.
   - Service Stopped State: 1-click background daemon bootstrap button (`startOllamaServer()`).
4. **Backend Streaming & Integration Tests**:
   - Tested in `backend/tests/test_ai_runtime.py`:
     - `test_ollama_pull_model_stream`: Validates NDJSON streaming chunks, byte counters, and percent calculation.
     - `test_pull_model_api_endpoint`: Validates FastAPI `/api/models/pull` SSE streaming formatting.
5. **Quality Assurance**:
   - Production Vite frontend compilation (`npm run build`) in 9.42s with 0 errors.
   - 48 unit and integration tests passed in 12.05s.
   - Zero flake8 warnings.
