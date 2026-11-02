"""
Aegis AI - One-Click Installer Generator & Desktop Packager.
Automates the compilation of a standalone, self-extracting Windows executable
installer (AegisAI-Setup.exe) with embedded assets, desktop shortcuts,
and Windows Add/Remove Programs integration.
"""

import hashlib
import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("aegis.installer")

CSC_PATH_X64 = r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe"
CSC_PATH_X86 = r"C:\Windows\Microsoft.NET\Framework\v4.0.30319\csc.exe"
VERSION = "0.2.0-alpha"


def find_csc_compiler() -> Optional[str]:
    """Finds the native Microsoft .NET C# compiler on Windows."""
    if os.path.exists(CSC_PATH_X64):
        return CSC_PATH_X64
    if os.path.exists(CSC_PATH_X86):
        return CSC_PATH_X86
    return None


def compute_sha256(file_path: Path) -> str:
    """Computes SHA-256 hash for file verification."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


class OneClickInstallerBuilder:
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).resolve().parent.parent.parent.parent
        self.releases_dir = self.project_root / "releases"
        self.assets_dir = self.project_root / "assets"
        self.scripts_dir = self.project_root / "scripts"

    def get_status(self) -> Dict[str, Any]:
        """Returns the current status of the built One-Click Installer."""
        self.releases_dir.mkdir(parents=True, exist_ok=True)
        setup_exe = self.releases_dir / "AegisAI-Setup.exe"
        versioned_exe = self.releases_dir / f"AegisAI-Setup-v{VERSION}.exe"

        target_file = setup_exe if setup_exe.exists() else (versioned_exe if versioned_exe.exists() else None)

        if not target_file or not target_file.exists():
            return {
                "available": False,
                "version": VERSION,
                "file_name": None,
                "file_path": None,
                "size_bytes": 0,
                "size_mb": 0.0,
                "sha256": None,
                "last_modified": None,
            }

        stat = target_file.stat()
        sha256 = compute_sha256(target_file)
        return {
            "available": True,
            "version": VERSION,
            "file_name": target_file.name,
            "file_path": str(target_file.resolve()),
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "sha256": sha256,
            "last_modified": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)),
        }

    def build_installer(self) -> Dict[str, Any]:
        """
        Builds the portable distribution bundle and compiles the standalone
        Windows One-Click Setup executable (AegisAI-Setup.exe).
        """
        csc = find_csc_compiler()
        if not csc:
            raise RuntimeError("Microsoft .NET Framework C# compiler (csc.exe) was not found on this system.")

        installer_cs = self.scripts_dir / "installer.cs"
        if not installer_cs.exists():
            raise FileNotFoundError(f"Installer source file not found at: {installer_cs}")

        icon_file = self.assets_dir / "icon.ico"
        if not icon_file.exists():
            raise FileNotFoundError(f"Icon file not found at: {icon_file}")

        self.releases_dir.mkdir(parents=True, exist_ok=True)

        # 1. Ensure portable package exists
        zip_pkg = self.releases_dir / f"Aegis-AI-v{VERSION}-Windows-x64-Portable.zip"
        if not zip_pkg.exists():
            logger.info("Portable archive not found. Invoking build_distribution.py...")
            import sys
            dist_script = self.scripts_dir / "build_distribution.py"
            subprocess.run([sys.executable, str(dist_script)], cwd=str(self.project_root), check=True)

        if not zip_pkg.exists():
            raise FileNotFoundError(f"Failed to generate portable package at: {zip_pkg}")

        # 2. Output targets
        setup_exe = self.releases_dir / "AegisAI-Setup.exe"
        versioned_exe = self.releases_dir / f"AegisAI-Setup-v{VERSION}.exe"

        # 3. Compile standalone C# installer with embedded ZIP package
        cmd = [
            csc,
            "/nologo",
            "/target:winexe",
            "/platform:x64",
            "/optimize+",
            f"/resource:{zip_pkg},AegisPackage",
            f"/win32icon:{icon_file}",
            "/r:System.Windows.Forms.dll",
            "/r:System.Drawing.dll",
            "/r:System.IO.Compression.dll",
            "/r:System.IO.Compression.FileSystem.dll",
            "/r:Microsoft.CSharp.dll",
            f"/out:{setup_exe}",
            str(installer_cs),
        ]

        logger.info(f"Compiling One-Click Installer via {csc}...")
        result = subprocess.run(cmd, cwd=str(self.project_root), capture_output=True, text=True)

        if result.returncode != 0:
            logger.error(f"CSC Compilation failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}")
            raise RuntimeError(f"Installer compilation failed with code {result.returncode}: {result.stderr}")

        # 4. Copy to versioned executable as well
        import shutil
        shutil.copy2(setup_exe, versioned_exe)

        # 5. Update SHA256 checksums
        sha256_setup = compute_sha256(setup_exe)
        sha256_ver = compute_sha256(versioned_exe)
        checksum_file = self.releases_dir / "SHA256SUMS.txt"

        lines = []
        if checksum_file.exists():
            with open(checksum_file, "r", encoding="utf-8") as f:
                for line in f:
                    if not any(name in line for name in ["AegisAI-Setup.exe", versioned_exe.name]):
                        lines.append(line.strip())

        lines.append(f"{sha256_setup}  {setup_exe.name}")
        lines.append(f"{sha256_ver}  {versioned_exe.name}")

        with open(checksum_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

        logger.info(f"One-Click Installer built successfully: {setup_exe.name} ({setup_exe.stat().st_size} bytes)")
        return self.get_status()

    def open_folder(self) -> Dict[str, Any]:
        """Opens Windows Explorer with the installer file selected."""
        status = self.get_status()
        if not status["available"] or not status["file_path"]:
            # If installer file does not exist, just open the releases folder
            subprocess.run(["explorer.exe", str(self.releases_dir.resolve())])
            return {"status": "opened_dir", "path": str(self.releases_dir.resolve())}

        file_path = status["file_path"]
        subprocess.run(["explorer.exe", f"/select,{file_path}"])
        return {"status": "opened_file", "path": file_path}

    def launch_installer(self) -> Dict[str, Any]:
        """Launches the generated installer executable."""
        status = self.get_status()
        if not status["available"] or not status["file_path"]:
            raise FileNotFoundError("One-Click Installer has not been built yet.")

        file_path = status["file_path"]
        subprocess.Popen([file_path], cwd=str(self.releases_dir))
        return {"status": "launched", "path": file_path}


installer_builder = OneClickInstallerBuilder()

