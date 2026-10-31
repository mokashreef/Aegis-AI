# Milestone 3: Autonomous Agent Workflows & Browser Engine

## Overview
- **Phase**: Autonomous Agency & Web Intelligence
- **Target Timeline**: Months 7–9 (Q3)
- **Status**: PLANNED
- **Goal**: Empower Aegis AI with long-running agent workflows, Playwright headless browser navigation, and offline wake-word speech activation.

---

## Deliverables & Work Items

| Work Item ID | Feature Description | Complexity | Priority | Subsystem |
| :--- | :--- | :--- | :--- | :--- |
| **M3-AGENT-01** | Plan-and-Solve Multi-Step Agent Loop | High | P0 | `aegis_core.agent.planner` |
| **M3-AGENT-02** | Background Task Supervisor & Tray Alerts | Medium | P0 | `aegis_core.agent.tasks` |
| **M3-WEB-01** | Playwright Chromium Automation Suite | High | P0 | `aegis_core.automation.browser` |
| **M3-WEB-02** | Clean DOM & Readability Article Extractor | Medium | P1 | `aegis_core.knowledge.web_extractor` |
| **M3-VOICE-01** | Offline Wake Word ("Hey Aegis") | High | P1 | `aegis_core.voice.wake_word` |
| **M3-VOICE-02** | Silero VAD (Voice Activity Detection) | Medium | P1 | `aegis_core.voice.vad` |

---

## Technical Architecture Notes

### Playwright Headless Browser Sandbox
Playwright drives an isolated Chromium instance configured with:
- Strict local network isolation options
- Headless execution with screenshot state dumps
- DOM accessibility tree extraction rather than raw HTML to minimize token consumption
- Safety confirmation when navigating to authenticated domains or executing purchase flows.

