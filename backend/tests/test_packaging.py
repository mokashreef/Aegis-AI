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


def test_ensure_frontend_built_verification():
    # Should not raise exception
    ensure_frontend_built()
    dist_index = PROJECT_ROOT / "apps" / "desktop-ui" / "dist" / "index.html"
    assert dist_index.exists()


def test_ensure_models_present_verification():
    # Core models must exist
    ensure_models_present()
    models_dir = PROJECT_ROOT / "data" / "models" / "wakeword"
    for name in ["melspectrogram.onnx", "embedding_model.onnx", "hey_jarvis_v0.1.onnx", "alexa_v0.1.onnx"]:
        assert (models_dir / name).exists()
