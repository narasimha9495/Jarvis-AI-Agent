# Jarvis AI Setup Script (Windows)
Write-Host 'Setting up Jarvis AI Agent...' -ForegroundColor Cyan
if (-not (Test-Path 'venv')) { python -m venv venv }
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
if (-not (Test-Path '.env')) { Copy-Item '.env.example' '.env' }
Write-Host 'Setup complete! Run: uvicorn app.main:app --reload' -ForegroundColor Green
