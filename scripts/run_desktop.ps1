# Aegis AI - Windows Desktop Companion Launcher

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "         Launching Aegis AI Desktop       " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

if (-not (Test-Path ".\.venv\Scripts\Activate.ps1")) {
    Write-Host "Error: Virtual environment not found. Please run .\scripts\setup_env.ps1 first." -ForegroundColor Red
    exit 1
}

.\.venv\Scripts\Activate.ps1
Write-Host "Starting native desktop companion overlay..." -ForegroundColor Green
Write-Host "Press Alt + Space anywhere in Windows to toggle Aegis AI." -ForegroundColor Yellow
Write-Host "Press ESC or click the X button to dismiss." -ForegroundColor Yellow

python aegis.py

