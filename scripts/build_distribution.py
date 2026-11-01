"""
Aegis AI - Automated Windows Distribution & Portable Release Packager.
Assembles the complete zero-friction distribution bundle, validates bundled
frontend assets, bundles local ONNX models, and generates release archives with SHA256 hashes.
"""

import hashlib
import os
import shutil
import subprocess
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BUILD_DIR = PROJECT_ROOT / "build" / "AegisAI"
RELEASES_DIR = PROJECT_ROOT / "releases"
VERSION = "0.2.0-alpha"


def log(msg: str) -> None:
    print(f"[Aegis Packager] {msg}")


def ensure_frontend_built() -> None:
    """Verifies or builds the React desktop HUD distribution bundle."""
    dist_dir = PROJECT_ROOT / "apps" / "desktop-ui" / "dist"
    index_html = dist_dir / "index.html"

    if not index_html.exists():
        log("Desktop UI bundle missing. Compiling frontend assets...")
        ui_dir = PROJECT_ROOT / "apps" / "desktop-ui"
        subprocess.run(["npm", "run", "build"], cwd=str(ui_dir), check=True, shell=True)
        log("Desktop UI build completed.")
    else:
        log("Desktop UI bundle verified.")


def ensure_models_present() -> None:
    """Verifies that core offline wake-word ONNX models are present in the source."""
    models_dir = PROJECT_ROOT / "data" / "models" / "wakeword"
    models_dir.mkdir(parents=True, exist_ok=True)
    required = ["melspectrogram.onnx", "embedding_model.onnx", "hey_jarvis_v0.1.onnx", "alexa_v0.1.onnx"]

    for name in required:
        model_file = models_dir / name
        if not model_file.exists():
            log(f"Warning: {name} not found in {models_dir}. Ensuring model presence via engine...")
            from aegis_core.voice.wake_word import wake_word_engine

            wake_word_engine.ensure_models_downloaded()
            break
    log("Acoustic wake-word models verified.")


def stage_distribution_files() -> Path:
    """Copies all production runtime files into the staging directory."""
    if BUILD_DIR.exists():
        shutil.rmtree(BUILD_DIR)
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    log(f"Staging release files in {BUILD_DIR}...")

    # Root files
    for f in ["AegisAI.exe", "aegis.py", "run.bat", "AegisAI.vbs", "README.md", "CHANGELOG.md", "LICENSE"]:
        src = PROJECT_ROOT / f
        if src.exists():
            shutil.copy2(src, BUILD_DIR / f)

    # Backend package (ignore caches)
    def ignore_patterns(folder, contents):
        ignored = []
        for c in contents:
            if c in ["__pycache__", ".pytest_cache", ".coverage"] or c.endswith(".pyc"):
                ignored.append(c)
        return ignored

    shutil.copytree(PROJECT_ROOT / "backend", BUILD_DIR / "backend", ignore=ignore_patterns)

    # Compiled UI dist
    shutil.copytree(PROJECT_ROOT / "apps" / "desktop-ui" / "dist", BUILD_DIR / "apps" / "desktop-ui" / "dist")

    # Wake word models
    models_src = PROJECT_ROOT / "data" / "models" / "wakeword"
    if models_src.exists():
        shutil.copytree(models_src, BUILD_DIR / "data" / "models" / "wakeword")

    # Assets & Icons
    assets_src = PROJECT_ROOT / "assets"
    if assets_src.exists():
        shutil.copytree(assets_src, BUILD_DIR / "assets")

    # Scripts
    scripts_dest = BUILD_DIR / "scripts"
    scripts_dest.mkdir(parents=True, exist_ok=True)
    for s in ["run_desktop.ps1", "setup_env.ps1"]:
        src_s = PROJECT_ROOT / "scripts" / s
        if src_s.exists():
            shutil.copy2(src_s, scripts_dest / s)

    log("Staging completed successfully.")
    return BUILD_DIR


def create_portable_zip(staged_dir: Path) -> Path:
    """Packs the staged directory into a single release zip archive."""
    RELEASES_DIR.mkdir(parents=True, exist_ok=True)
    zip_filename = f"Aegis-AI-v{VERSION}-Windows-x64-Portable.zip"
    zip_path = RELEASES_DIR / zip_filename

    log(f"Compressing portable distribution archive: {zip_path.name}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zipf:
        for root, _, files in os.walk(staged_dir):
            for file in files:
                abs_path = Path(root) / file
                rel_path = abs_path.relative_to(staged_dir.parent)
                zipf.write(abs_path, str(rel_path))

    size_mb = zip_path.stat().st_size / (1024 * 1024)
    log(f"Created portable release: {zip_filename} ({size_mb:.2f} MB)")
    return zip_path


def compute_checksum(file_path: Path) -> str:
    """Computes SHA-256 hash for release verification."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def main():
    log(f"Starting Aegis AI v{VERSION} Packaging & Distribution Build...")
    ensure_frontend_built()
    ensure_models_present()
    staged = stage_distribution_files()
    zip_archive = create_portable_zip(staged)

    # Generate checksum file
    sha256 = compute_checksum(zip_archive)
    checksum_file = RELEASES_DIR / "SHA256SUMS.txt"
    with open(checksum_file, "w", encoding="utf-8") as f:
        f.write(f"{sha256}  {zip_archive.name}\n")

    log(f"SHA-256: {sha256}")
    log(f"Checksum file: {checksum_file.resolve()}")
    log("Distribution build successfully finished!")


if __name__ == "__main__":
    main()
