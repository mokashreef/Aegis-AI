"""
Aegis AI - Wake Word Empirical Performance & Latency Benchmark.
Measures ONNX keyword inference latency, energy gating speed, memory footprint, and CPU usage.
"""

import json
import os
import time
from pathlib import Path
import numpy as np
import psutil
from aegis_core.voice.wake_word import WakeWordEngine, WakeWordListener


def benchmark_wake_word():
    results = {}
    proc = psutil.Process(os.getpid())

    # 1. Initialization Benchmark
    t0 = time.perf_counter()
    engine = WakeWordEngine()
    loaded = engine.load_models()
    init_latency_ms = (time.perf_counter() - t0) * 1000

    results["initialization"] = {
        "success": loaded,
        "latency_ms": round(init_latency_ms, 2),
        "available_models": list(engine._classifiers.keys()),
    }

    # 2. Silence Gating Benchmark (RMS gate bypass)
    silence_chunk = np.zeros(1280, dtype=np.float32)
    t0 = time.perf_counter()
    iterations = 500
    for _ in range(iterations):
        engine.process_frame(silence_chunk, silence_threshold=0.005)
    silence_latency_us = ((time.perf_counter() - t0) / iterations) * 1_000_000

    results["silence_gating"] = {
        "iterations": iterations,
        "avg_latency_microseconds": round(silence_latency_us, 3),
        "status": "PASS" if silence_latency_us < 100 else "SLOW",
    }

    # 3. Active Acoustic Inference Benchmark (Full ONNX Mel -> Emb -> Cls)
    speech_chunk = (np.random.randn(1280) * 0.1).astype(np.float32)
    t0 = time.perf_counter()
    onnx_iterations = 100
    for _ in range(onnx_iterations):
        engine.process_frame(speech_chunk, silence_threshold=0.0001)
    inference_latency_ms = ((time.perf_counter() - t0) / onnx_iterations) * 1000

    results["acoustic_inference"] = {
        "iterations": onnx_iterations,
        "avg_latency_ms": round(inference_latency_ms, 2),
        "frame_duration_ms": 80.0,
        "realtime_factor": round(inference_latency_ms / 80.0, 4),
        "status": "PASS" if inference_latency_ms < 20.0 else "SLOW",
    }

    # 4. Listener Lifecycle & Threading
    listener = WakeWordListener(engine=engine, wake_word="hey_jarvis", confidence_threshold=0.55)
    t0 = time.perf_counter()
    started = listener.start()
    time.sleep(0.5)  # Listen for 500ms
    is_running = listener.is_running()
    listener.stop()
    teardown_ms = (time.perf_counter() - t0) * 1000

    results["listener_thread"] = {
        "started": started,
        "is_running_during_stream": is_running,
        "stream_cycle_latency_ms": round(teardown_ms, 2),
    }

    # 5. Process Telemetry
    mem_info = proc.memory_info()
    results["resource_telemetry"] = {
        "rss_memory_mb": round(mem_info.rss / (1024 * 1024), 2),
        "cpu_percent": proc.cpu_percent(interval=0.1),
    }

    # Save validation evidence
    evidence_path = Path(".github/validation_evidence/section2b_wake_word.json")
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence_path.write_text(json.dumps(results, indent=2), encoding="utf-8")

    print("\n================ WAKE WORD BENCHMARK REPORT ================")
    print(f"Engine Init Latency:      {results['initialization']['latency_ms']} ms")
    print(f"Silence Gate Latency:     {results['silence_gating']['avg_latency_microseconds']} us")
    print(f"Acoustic Frame Latency:   {results['acoustic_inference']['avg_latency_ms']} ms (Budget: 80.0 ms)")
    print(f"Realtime Factor:          {results['acoustic_inference']['realtime_factor']}x (Realtime < 1.0)")
    print(f"Listener Start/Stop:      {results['listener_thread']['stream_cycle_latency_ms']} ms")
    print(f"Process RAM (RSS):        {results['resource_telemetry']['rss_memory_mb']} MB")
    print(f"Evidence Saved:           {evidence_path.resolve()}")
    print("============================================================\n")


if __name__ == "__main__":
    benchmark_wake_word()

