# ============================================
# AI Forensic Analysis Unit — 启动脚本
# ============================================

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  AI FORENSIC ANALYSIS UNIT" -ForegroundColor White
Write-Host "  AI图像真实性刑侦系统 v1.0" -ForegroundColor Gray
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check for .env
if (-not (Test-Path ".env")) {
    Write-Host "[!] .env not found, copying from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "[!] Please edit .env with your API keys before running." -ForegroundColor Yellow
    Write-Host ""
}

# Start backend
Write-Host "[1/2] Starting backend (FastAPI)..." -ForegroundColor Green
$backendProc = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\backend'; python -m venv venv 2>`$null; .\venv\Scripts\Activate.ps1; pip install -r requirements.txt -q; uvicorn main:app --reload --host 0.0.0.0 --port 8001" -PassThru

# Start frontend
Write-Host "[2/2] Starting frontend (Next.js)..." -ForegroundColor Green
$frontendProc = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD\frontend'; npm install; npm run dev" -PassThru

Write-Host ""
Write-Host "----------------------------------------" -ForegroundColor Cyan
Write-Host "  Backend:  http://localhost:8001" -ForegroundColor White
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "  API Docs: http://localhost:8001/docs" -ForegroundColor Gray
Write-Host "----------------------------------------" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press any key to stop all services..." -ForegroundColor DarkGray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Cleanup — 只结束本脚本启动的两个窗口及其子进程，不影响机器上其他 python/node
foreach ($proc in @($backendProc, $frontendProc)) {
    if ($proc -and -not $proc.HasExited) {
        taskkill /PID $proc.Id /T /F 2>$null | Out-Null
    }
}
Write-Host "Services stopped." -ForegroundColor Yellow
