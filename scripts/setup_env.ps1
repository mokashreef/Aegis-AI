# Aegis AI - Windows Development & Runtime Setup Script

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "     Aegis AI - Environment Setup        " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Check Python
Write-Host "`n[1/4] Checking Python 3.11+..." -ForegroundColor Yellow
$pyVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Python 3.11+ is required but not found in PATH." -ForegroundColor Red
    exit 1
}
Write-Host "Found: $pyVersion" -ForegroundColor Green

# 2. Virtual Environment Setup
Write-Host "`n[2/4] Initializing Python Virtual Environment (.venv)..." -ForegroundColor Yellow
if (-not (Test-Path ".venv")) {
    python -m venv .venv
}
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r backend\requirements.txt
Write-Host "Python dependencies installed successfully." -ForegroundColor Green

# 3. Frontend Node Dependencies & Production Bundle Build
Write-Host "`n[3/4] Building Desktop UI Bundle (apps/desktop-ui)..." -ForegroundColor Yellow
Push-Location apps/desktop-ui
npm install
npm run build
Pop-Location
Write-Host "Frontend production bundle built successfully." -ForegroundColor Green

# 4. Probe Local Ollama
Write-Host "`n[4/4] Probing Local Ollama Engine..." -ForegroundColor Yellow
$ollamaCmd = Get-Command ollama -ErrorAction SilentlyContinue
if ($ollamaCmd) {
    Write-Host "Ollama is installed at $($ollamaCmd.Source)." -ForegroundColor Green
    Write-Host "For offline local intelligence, recommended: 'ollama run qwen2.5:1.5b'" -ForegroundColor Cyan
} else {
    Write-Host "Ollama was not detected in PATH." -ForegroundColor Yellow
    Write-Host "Aegis AI will automatically utilize free anonymous fallback providers (Pollinations AI)." -ForegroundColor Yellow
    Write-Host "To enable air-gapped local intelligence, install Ollama from https://ollama.com" -ForegroundColor Cyan
}

Write-Host "`n==========================================" -ForegroundColor Green
Write-Host "Setup Completed! Run '.\scripts\run_desktop.ps1' or 'python aegis.py' to launch." -ForegroundColor Green
Write-Host "Press Alt + Space anywhere in Windows to summon the companion." -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Green
