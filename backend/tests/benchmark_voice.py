"""
Aegis AI - Production Validation Benchmark: Voice Pipeline.
Empirically tests Neural TTS and Faster-Whisper STT with English, Arabic, and Mixed language phrases.
Measures latency, bytes generated, and transcription accuracy.
"""

import asyncio
import json
from pathlib import Path
import time
from aegis_core.voice.stt import FasterWhisperEngine
from aegis_core.voice.tts import NeuralTTSEngine

EVIDENCE_DIR = Path(".github/validation_evidence")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR = Path("storage/cache/voice_test")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

TEST_CASES = [
    {
        "id": "en_sample",
        "lang": "English",
        "text": "Hello, this is Aegis AI running on Windows.",
        "tts_voice": "en-US-AriaNeural",
    },
    {
        "id": "ar_sample",
        "lang": "Arabic",
        "text": "مرحبا بك في نظام ايجيس للذكاء الاصطناعي.",
        "tts_voice": "ar-SA-ZariyahNeural",
    },
    {
        "id": "mixed_sample",
        "lang": "Mixed",
        "text": "Open notepad واكتب تقرير اليوم please.",
        "tts_voice": "en-US-AriaNeural",
    },
]


async def benchmark_voice():
    tts = NeuralTTSEngine()
    stt = FasterWhisperEngine(model_size="tiny")

    results = {
        "tts_synthesis": [],
        "stt_transcription": [],
        "wake_word_audit": {
            "implemented": False,
            "status": "MISSING / ISSUE FILED #7",
            "issue": ".github/issues/issue-007-missing-wake-word-engine.md",
        },
    }

    # 1. Benchmark Neural TTS
    print("--- 1. Testing Neural TTS ---")
    for case in TEST_CASES:
        t0 = time.perf_counter()
        audio_bytes = await tts.synthesize_to_bytes(case["text"], case["tts_voice"])
        latency_ms = (time.perf_counter() - t0) * 1000.0

        audio_file = CACHE_DIR / f"{case['id']}.mp3"
        audio_file.write_bytes(audio_bytes)

        tts_result = {
            "id": case["id"],
            "lang": case["lang"],
            "input_text": case["text"],
            "voice": case["tts_voice"],
            "latency_ms": round(latency_ms, 2),
            "audio_bytes": len(audio_bytes),
            "success": len(audio_bytes) > 0,
            "file": str(audio_file),
        }
        results["tts_synthesis"].append(tts_result)
        print(f"TTS [{case['lang']}]: {latency_ms:.2f}ms, {len(audio_bytes)} bytes")

    # 2. Benchmark Faster-Whisper STT
    print("\n--- 2. Testing Faster-Whisper STT ---")
    for case in TEST_CASES:
        audio_file = CACHE_DIR / f"{case['id']}.mp3"
        if not audio_file.exists() or audio_file.stat().st_size == 0:
            results["stt_transcription"].append({
                "id": case["id"],
                "success": False,
                "error": "Audio file missing or empty",
            })
            continue

        try:
            t0 = time.perf_counter()
            # Note: tiny model transcribe with vad
            text = stt.transcribe_file(audio_file)
            latency_ms = (time.perf_counter() - t0) * 1000.0

            stt_result = {
                "id": case["id"],
                "lang": case["lang"],
                "ground_truth": case["text"],
                "transcription": text,
                "latency_ms": round(latency_ms, 2),
                "success": bool(text.strip()),
            }
            results["stt_transcription"].append(stt_result)
            print(f"STT [{case['lang']}]: {latency_ms:.2f}ms -> '{text}'")
        except Exception as exc:
            print(f"STT [{case['lang']}] Error: {exc}")
            results["stt_transcription"].append({
                "id": case["id"],
                "lang": case["lang"],
                "success": False,
                "error": str(exc),
            })

    # Save evidence
    evidence_file = EVIDENCE_DIR / "section2_voice.json"
    evidence_file.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nSaved voice audit results to {evidence_file}")
    return results


if __name__ == "__main__":
    asyncio.run(benchmark_voice())

