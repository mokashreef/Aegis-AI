## Description

Briefly describe the purpose of this Pull Request, what bug it resolves, or what new capability it introduces.

Closes # (issue number if applicable)

## Type of Change

- [ ] 🐛 Bug fix (non-breaking change which fixes an issue)
- [ ] ✨ New feature (non-breaking change which adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📚 Documentation update
- [ ] ⚡ Performance optimization
- [ ] 🧪 Testing & QA addition
- [ ] 🧩 Plugin ecosystem update

## Architectural Subsystem Affected

- [ ] Desktop Overlay / Tauri Bridge
- [ ] React / TypeScript Frontend
- [ ] Python Core Daemon / FastAPI Gateway
- [ ] AI Runtime & Fallback Engine
- [ ] Voice STT / TTS Pipeline
- [ ] Windows Desktop Automation Engine
- [ ] Playwright Browser Automation
- [ ] Memory & Vector Search
- [ ] Dynamic Plugin System

## Zero-Cost & Local Execution Verification

- [ ] Verified that this change operates with zero required paid API keys.
- [ ] Works with local Ollama or free fallback providers without vendor lock-in.

## Testing Checklist

- [ ] Unit tests added / updated and passing (`pytest backend/tests`)
- [ ] Frontend type-check & lint passing (`npm run check` / `npm run lint`)
- [ ] Manual verification performed on Windows desktop
- [ ] No regression introduced to existing hotkeys or automation flows

## Screenshots / Video / Demos (if applicable)

*Add screenshots of UI changes, overlay states, or CLI logs.*

## Checklist

- [ ] My code adheres to the project's [Code of Conduct](CODE_OF_CONDUCT.md) and [Contributing Guidelines](CONTRIBUTING.md).
- [ ] I have commented my code, particularly explaining "why" rather than just "what".
- [ ] I have updated the documentation in `docs/` and `CHANGELOG.md` accordingly.
- [ ] All new and existing tests pass.

