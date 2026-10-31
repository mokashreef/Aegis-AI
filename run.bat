@echo off
cd /d "%~dp0"
echo ==========================================
echo       Launching Aegis AI Desktop
echo ==========================================
echo.

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found in .venv!
    echo Please run setup first.
    pause
    exit /b 1
)

echo Starting native companion overlay...
echo Press Alt + Space anywhere in Windows to toggle Aegis AI.
echo Press ESC to hide.
echo.
".venv\Scripts\python.exe" aegis.py
pause
