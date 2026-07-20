# HIR AI Document Intelligence Platform - Start Script
# This PowerShell script launches both the backend and frontend dev servers in separate windows.

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Starting HIR AI Document Intelligence Platform..." -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Start Backend Server
Write-Host "[1/2] Launching Backend Server on Port 8002..." -ForegroundColor Yellow
$backendCommand = "cd backend; `$env:PYTHONPATH='.'; `$env:DATABASE_URL_OVERRIDE='sqlite+aiosqlite:///./hir_dev.db'; uv run python run_server.py"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand

# 2. Start Frontend Dev Server
Write-Host "[2/2] Launching Frontend Development Server on Port 5173..." -ForegroundColor Yellow
$frontendCommand = "cd frontend; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCommand

# 3. Complete
Write-Host ""
Write-Host "✔ Platform launched successfully!" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "Access Points:" -ForegroundColor Green
Write-Host " - Frontend Portal: http://localhost:5173/" -ForegroundColor White
Write-Host " - Backend Swagger API: http://localhost:8002/docs" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "Separate PowerShell windows have been opened for the processes." -ForegroundColor Gray
Write-Host "Close those windows to stop the servers." -ForegroundColor Gray
