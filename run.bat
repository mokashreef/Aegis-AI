@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo ===================================================
    echo  [ERROR] Virtual environment not found in .venv!
    echo  Please run .\scripts\setup_env.ps1 first.
    echo ===================================================
    pause
    exit /b 1
)

:: Launch completely silently without keeping or flashing any console window
if exist "AegisAI.vbs" (
    start "" wscript.exe "%~dp0AegisAI.vbs"
    exit
)

if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" aegis.py
    exit
) else (
    start "" ".venv\Scripts\python.exe" aegis.py
    exit
)
