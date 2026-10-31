# Security Policy

Aegis AI is an open-source, local-first Windows AI companion equipped with system automation, clipboard access, voice capabilities, and tool execution. We treat the security, privacy, and integrity of the host operating system with the utmost gravity.

## Supported Versions

Only the latest release and the current active development branch receive active security patches.

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1.0 | :x:                |

## Architectural Security Model

Aegis AI operates under five immutable security principles:

1. **Zero External Data Exfiltration**:
   - By default, all conversations, vector embeddings, and memory states reside solely in your local SQLite database (`storage/aegis.db`).
   - No telemetry, analytics, or conversational tokens are transmitted to proprietary cloud backends without explicit user consent.
2. **Zero Mandatory Paid Services & Secrets**:
   - No API keys are required for out-of-the-box operation.
   - Any optionally added third-party keys are stored locally using Windows DPAPI (Data Protection API) or encrypted configuration files.
3. **Execution Guardrails & Destructive Action Interception**:
   - Autonomous agent actions that modify files, execute shell commands, or interact with external applications run through a granular permission layer.
   - Critical operations (e.g., permanent file deletion, process termination, system configuration changes) enforce user confirmation prompts.
4. **Least Privilege Principle**:
   - Aegis AI does not require and must never run under Administrator elevation for daily operations.
   - Any tool requiring elevated Windows privileges must prompt the user via Windows UAC dialogs explicitly.
5. **Prompt Injection & Tool Isolation**:
   - Inputs retrieved from external web pages, emails, or documents are quarantined before being fed back into reasoning loops to mitigate Indirect Prompt Injection (IPI).

## Reporting a Vulnerability

If you discover a security vulnerability within Aegis AI, please **do not** open a public issue on GitHub.

Instead, please report the vulnerability privately via:
- **GitHub Security Advisories**: Navigate to the repository's "Security" tab and select "Report a vulnerability".
- **Security Response Team**: Email security advisories directly to the maintainers at `security@aegis-ai.local` (or through GitHub private disclosure).

### When reporting, please provide:
- A clear description of the vulnerability and its potential impact.
- Step-by-step reproduction instructions or a minimal Proof of Concept (PoC).
- Your operating system environment (Windows version, build number).
- Affected version or commit hash.

### Response Timetable
- **Initial Acknowledgment**: Within 48 hours.
- **Triage & Assessment**: Within 5 business days.
- **Fix & Advisory Release**: Coordinated disclosure within 30 days of validation.

