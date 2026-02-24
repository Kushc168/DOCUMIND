$ErrorActionPreference = "Stop"

Write-Host "Starting DocuMind locally..." -ForegroundColor Cyan

if (!(Test-Path ".venv")) {
  Write-Host "Creating venv..." -ForegroundColor Yellow
  python -m venv .venv
}

Write-Host "Installing backend core deps..." -ForegroundColor Yellow
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-core.txt --default-timeout=120
Write-Host "Optional heavy deps (PDF/Word conversion) can be installed with:" -ForegroundColor DarkYellow
Write-Host ".\.venv\Scripts\python.exe -m pip install -r backend\requirements-heavy.txt --default-timeout=300" -ForegroundColor DarkYellow
Write-Host "Optional OCR deps (PDF -> Text) can be installed with:" -ForegroundColor DarkYellow
Write-Host ".\.venv\Scripts\python.exe -m pip install -r backend\requirements-ocr.txt --default-timeout=300" -ForegroundColor DarkYellow
Write-Host "Optional Gemini chat deps can be installed with:" -ForegroundColor DarkYellow
Write-Host ".\.venv\Scripts\python.exe -m pip install -r backend\requirements-gemini.txt --default-timeout=300" -ForegroundColor DarkYellow
Write-Host "Optional Groq chat deps can be installed with:" -ForegroundColor DarkYellow
Write-Host ".\.venv\Scripts\python.exe -m pip install -r backend\requirements-groq.txt --default-timeout=300" -ForegroundColor DarkYellow

Write-Host "Starting backend (FastAPI)..." -ForegroundColor Green
Start-Process -NoNewWindow -FilePath .\.venv\Scripts\python.exe -ArgumentList "-m uvicorn app.main:app --reload --app-dir backend"

Write-Host "Starting frontend (Vite)..." -ForegroundColor Green
Start-Process -NoNewWindow -FilePath npm -ArgumentList "--prefix frontend install"
Start-Process -NoNewWindow -FilePath npm -ArgumentList "--prefix frontend run dev"

Write-Host "Open http://localhost:5173" -ForegroundColor Cyan
