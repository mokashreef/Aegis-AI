"""
Unit and integration tests for Aegis AI distribution packaging.
"""

import hashlib
import sys
from pathlib import Path

# Ensure scripts dir is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from build_distribution import (  # noqa: E402
    compute_checksum,
    ensure_frontend_built,
    ensure_models_present,
)


def test_checksum_computation(tmp_path):
    test_file = tmp_path / "test_artifact.bin"
    test_content = b"Aegis AI Zero Friction Release"
    test_file.write_bytes(test_content)

    expected_hash = hashlib.sha256(test_content).hexdigest()
    computed = compute_checksum(test_file)
    assert computed == expected_hash


def test_ensure_frontend_built_verification(tmp_path, monkeypatch):
    import build_distribution

    mock_dist = tmp_path / "apps" / "desktop-ui" / "dist"
    mock_dist.mkdir(parents=True, exist_ok=True)
    dist_index = mock_dist / "index.html"
    dist_index.write_text("<!doctype html><html><body>Aegis HUD</body></html>", encoding="utf-8")

    monkeypatch.setattr(build_distribution, "PROJECT_ROOT", tmp_path)
    ensure_frontend_built()
    assert dist_index.exists()


def test_ensure_models_present_verification(tmp_path, monkeypatch):
    import build_distribution

    mock_models = tmp_path / "data" / "models" / "wakeword"
    mock_models.mkdir(parents=True, exist_ok=True)
    required = ["melspectrogram.onnx", "embedding_model.onnx", "hey_jarvis_v0.1.onnx", "alexa_v0.1.onnx"]
    for name in required:
        (mock_models / name).write_bytes(b"mock_onnx_model")

    monkeypatch.setattr(build_distribution, "PROJECT_ROOT", tmp_path)
    ensure_models_present()
    for name in required:
        assert (mock_models / name).exists()
