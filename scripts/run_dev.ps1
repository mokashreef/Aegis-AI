# Aegis AI - Local Development Launcher

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "     Starting Aegis AI Dev Environment    " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Activate venv
if (-not (Test-Path ".\.venv\Scripts\Activate.ps1")) {
    Write-Host "Virtual environment not detected. Running setup first..." -ForegroundColor Yellow
    .\scripts\setup_env.ps1
}

# 2. Launch Backend Daemon
Write-Host "`n[1/2] Starting Aegis Core Daemon on http://127.0.0.1:8420..." -ForegroundColor Green
$backendProcess = Start-Process -FilePath ".\.venv\Scripts\python.exe" -ArgumentList "-m", "backend.aegis_core.main" -PassThru -NoNewWindow

# 3. Launch Frontend UI
Write-Host "[2/2] Starting Vite Frontend on http://localhost:5173..." -ForegroundColor Green
Push-Location apps/desktop-ui
try {
    npm run dev
} finally {
    Pop-Location
    if ($backendProcess -and -not $backendProcess.HasExited) {
        Write-Host "Stopping Aegis Core Daemon (PID: $($backendProcess.Id))..." -ForegroundColor Yellow
        Stop-Process -Id $backendProcess.Id -Force
    }
}
