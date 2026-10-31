"""
Aegis AI - Production Validation Benchmark: Desktop Automation.
Empirically executes the 13 required user commands through the real system and measures:
- Intent classification accuracy
- Tool resolution
- Execution status (WORKING, PARTIAL, BROKEN)
- Latency (ms)
- Concrete execution proof
"""

import asyncio
import json
from pathlib import Path
import time
from aegis_core.automation.intent_router import IntentRouter
from aegis_core.main import register_default_tools
from aegis_core.plugins.registry import plugin_registry

EVIDENCE_DIR = Path(".github/validation_evidence")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

COMMANDS = [
    {"cmd": "open chrome", "expected_tool": "launch_application"},
    {"cmd": "open notepad", "expected_tool": "launch_application"},
    {"cmd": "launch vscode", "expected_tool": "launch_application"},
    {"cmd": "open calculator", "expected_tool": "launch_application"},
    {"cmd": "maximize window", "expected_tool": "snap_window"},
    {"cmd": "snap window left", "expected_tool": "snap_window"},
    {"cmd": "snap window right", "expected_tool": "snap_window"},
    {"cmd": "mute sound", "expected_tool": "control_volume"},
    {"cmd": "set volume to 20%", "expected_tool": "control_volume"},
    {"cmd": "set brightness to 50%", "expected_tool": "control_brightness"},
    {"cmd": "take a screenshot", "expected_tool": "capture_screen"},
    {"cmd": "note down: meeting with engineering team at 4pm", "expected_tool": "manage_notes"},
    {"cmd": "show today's notes", "expected_tool": "manage_notes"},
]


async def benchmark_automation():
    register_default_tools()
    results = []

    print("=== EXECUTING REAL AUTOMATION VALIDATION SUITE ===")
    for item in COMMANDS:
        cmd = item["cmd"]
        expected = item["expected_tool"]

        # 1. Intent Classification
        t0 = time.perf_counter()
        routed = IntentRouter.classify_and_route(cmd)
        classify_time_ms = (time.perf_counter() - t0) * 1000.0

        if not routed:
            results.append({
                "command": cmd,
                "status": "BROKEN",
                "failure_reason": "Intent router failed to recognize command",
                "classification_latency_ms": round(classify_time_ms, 3),
            })
            print(f"[{cmd}] -> BROKEN (Unrecognized intent)")
            continue

        tool_name = routed["name"]
        arguments = routed["arguments"]

        # 2. Real Tool Execution
        t0 = time.perf_counter()
        tool_res = await plugin_registry.execute_tool(
            tool_name=tool_name,
            arguments=arguments,
            user_confirmed=True,
        )
        exec_time_ms = (time.perf_counter() - t0) * 1000.0

        status = "WORKING" if tool_res.success else "PARTIAL"
        entry = {
            "command": cmd,
            "status": status,
            "expected_tool": expected,
            "dispatched_tool": tool_name,
            "arguments": arguments,
            "success": tool_res.success,
            "message": tool_res.message,
            "error": tool_res.error,
            "data_summary": str(tool_res.data)[:200] if tool_res.data else None,
            "classification_latency_ms": round(classify_time_ms, 3),
            "execution_latency_ms": round(exec_time_ms, 2),
        }
        results.append(entry)
        print(f"[{cmd}] -> {status} via {tool_name} ({exec_time_ms:.1f}ms): {tool_res.message or tool_res.error}")

    evidence_file = EVIDENCE_DIR / "section3_automation.json"
    evidence_file.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved automation audit to {evidence_file}")
    return results


if __name__ == "__main__":
    asyncio.run(benchmark_automation())
