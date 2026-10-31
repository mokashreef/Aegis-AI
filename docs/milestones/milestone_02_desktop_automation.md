# Milestone 2: Deep Windows Automation & Multimodal Knowledge

## Overview
- **Phase**: Multimodal & OS Mastery
- **Target Timeline**: Months 4–6 (Q2)
- **Status**: PLANNED
- **Goal**: Expand Aegis AI beyond simple process launching to deep UIAutomation, window tiling, screenshot understanding with local vision models, and local vector RAG.

---

## Deliverables & Work Items

| Work Item ID | Feature Description | Complexity | Priority | Subsystem |
| :--- | :--- | :--- | :--- | :--- |
| **M2-AUTO-01** | UIAutomation API Tree Inspector | High | P0 | `aegis_core.automation.ui_tree` |
| **M2-AUTO-02** | Coordinate-Free Element Click & Input | High | P0 | `aegis_core.automation.ui_actions` |
| **M2-AUTO-03** | Multi-Monitor Window Tiling & Snap Engine | Medium | P1 | `aegis_core.automation.window_manager` |
| **M2-KNOW-01** | Offline Screenshot Region Capture & OCR | Medium | P0 | `aegis_core.knowledge.ocr` |
| **M2-KNOW-02** | Local Vision-Language Model Integration | High | P1 | `aegis_core.ai_runtime.vision` |
| **M2-MEM-01** | Embedded Vector Database (SQLite-vec) | High | P0 | `aegis_core.memory.vector_store` |
| **M2-MEM-02** | Document Ingestion Pipeline (PDF, TXT, MD) | Medium | P1 | `aegis_core.knowledge.ingestion` |
| **M2-UI-01** | Desktop Snipping & Visual Inspection HUD | Medium | P1 | `apps/desktop-ui` |

---

## Technical Architecture Notes

### UIAutomation Tree Walking
Unlike brittle mouse coordinates that fail when window scales change, M2-AUTO-01 connects directly to Windows UIAutomation COM interfaces. It queries accessibility elements by AutomationId, Name, ClassName, and ControlType.

### Local Multimodal Vision (Zero API Keys)
Aegis AI will integrate Moondream and LLaVA through Ollama (`ollama run moondream`), giving the assistant visual reasoning over desktop windows without uploading screenshots to the cloud.
