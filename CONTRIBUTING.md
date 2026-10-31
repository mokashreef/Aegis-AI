# Contributing to Aegis AI

First off, thank you for considering contributing to **Aegis AI**! Our mission is to build the premier open-source, local-first Windows AI companion that empowers users with intelligent assistance, deep desktop automation, and zero mandatory subscription fees or API keys.

---

## Code of Conduct

By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

---

## Core Principles for Contributors

1. **Zero Mandatory API Keys**: Any feature or module contributed must be operable using local tools (Ollama, local speech models) or accessible free tiers (Pollinations, open inference endpoints). Paid integrations may only exist as optional plugins.
2. **Production-Grade Quality Only**:
   - No mock placeholders.
   - No `TODO` comments left behind in merged pull requests.
   - No pseudo-code.
   - Strict typing across Python (`mypy` / Pydantic) and TypeScript.
   - Comprehensive error handling with graceful fallbacks.
3. **GitHub as the Source of Truth**:
   - Every significant PR must reference an existing GitHub Issue or RFC.
   - All architectural decisions must be documented in `docs/` and referenced in commit history.

---

## Development Environment Setup

### Prerequisites
- **Operating System**: Windows 10/11 (64-bit)
- **Python**: 3.11+
- **Node.js**: 20+ (Node 22 LTS or Node 24 recommended)
- **Git**: 2.40+
- **Ollama**: (Recommended for local LLM inference) [ollama.com](https://ollama.com)
- **Rust & Cargo**: (For compiling the native Tauri desktop binary) [rustup.rs](https://rustup.rs)

### Clone & Branching
```powershell
# Clone the repository
git clone git@github.com:mokashreef/Aegis-AI.git
cd "Aegis AI"

# Create a feature branch
git checkout -b feat/my-awesome-feature
```

### Python Backend Setup
```powershell
# Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Upgrade pip and install development dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt
pip install pytest pytest-asyncio pytest-cov flake8
```

### Frontend UI Setup
```powershell
cd apps/desktop-ui
npm install
npm run dev
```

---

## Branching & Commit Conventions

We strictly adhere to the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat(scope): add Piper TTS streaming audio player`
- `fix(automation): handle minimized windows in UIAutomation focus`
- `docs(architecture): add sequence diagram for ReAct agent loop`
- `test(memory): add unit tests for SQLite vector retrieval`
- `refactor(ai_runtime): optimize token streaming fallback chain`

Branch naming format:
- `feat/<short-description>`
- `fix/<issue-number>-<short-description>`
- `docs/<doc-topic>`
- `refactor/<module-name>`

---

## Testing & Quality Assurance

Before submitting a Pull Request, ensure that all test suites and linters pass:

```powershell
# 1. Run Python unit tests with coverage
pytest backend/tests -v --cov=backend/aegis_core

# 2. Run Python linting
flake8 backend --max-line-length=120

# 3. Check Frontend TypeScript types
cd apps/desktop-ui
npm run check
npm run build
```

---

## Pull Request Process

1. Open an issue first to discuss non-trivial features or architectural changes.
2. Fill out the [Pull Request Template](.github/PULL_REQUEST_TEMPLATE.md) completely.
3. Ensure CI passes on all matrices (Ubuntu and Windows).
4. A maintainer will review your code for architectural consistency, safety, and performance.
5. Once approved, commits are squash-merged or rebased into `main`.

