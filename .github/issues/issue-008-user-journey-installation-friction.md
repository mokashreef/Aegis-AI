# Issue #8: User Journey & First-Time Installation Audit

- **Labels**: `ux`, `install`, `setup`, `friction`, `reality-check`
- **Milestone**: MVP Production Validation
- **Status**: OPEN / IDENTIFIED GAP
- **Branch**: `audit/product-validation-execution`

## Problem Analysis
A first-time Windows user attempting to install Aegis AI faces significant friction:

### Metrics
1. **Commands required**: 3 manual shell invocations (`git clone`, `.\scripts\setup_env.ps1`, `.\scripts\run_desktop.ps1`).
2. **Dependencies required**: 3 external runtimes (Git, Python 3.11+, Node.js 20+).
3. **Downloads required**: ~450 MB (Python pip dependencies including torch/onnx/ctranslate2, and npm packages).
4. **Failure Points**:
   - `setup_env.ps1` ran `npm install` but failed to run `npm run build`, leaving `apps/desktop-ui/dist` missing on fresh clones.
   - `setup_env.ps1` instructed users to run `run_dev.ps1` (browser-only Vite server) rather than the native desktop companion launcher `run_desktop.ps1`.
   - Normal Windows users expect a `.msi` or `.exe` installer (Winget), not a full Node.js + Python compilation pipeline.

### Immediate Remediations
1. Update `scripts/setup_env.ps1` to automatically execute `npm run build` and point to `.\scripts\run_desktop.ps1`.
2. Add a fallback check in `backend/aegis_core/main.py` that warns if `apps/desktop-ui/dist` is missing and builds it automatically if Node is available.
3. Package pre-built frontend bundle or MSIX/PyInstaller desktop executable in the next distribution milestone.
