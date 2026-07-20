# HIR AI Document Intelligence Platform - Start Script
# Launches backend and frontend dev servers in separate PowerShell windows.

Write-Host '==========================================================' -ForegroundColor Cyan
Write-Host 'Starting HIR AI Document Intelligence Platform...' -ForegroundColor Cyan
Write-Host '==========================================================' -ForegroundColor Cyan

# Resolve root directory from script location
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir

# 1. Start Backend Server
Write-Host '[1/2] Launching Backend Server on Port 8002...' -ForegroundColor Yellow
$backendDir = Join-Path $RootDir 'backend'
$backendCommand = 'cd ' + $backendDir + '; $env:PYTHONPATH=.; $env:DATABASE_URL_OVERRIDE=sqlite+aiosqlite:///./hir_dev.db; uv run python run_server.py'
Start-Process powershell -ArgumentList '-NoExit', '-Command', $backendCommand

# 2. Start Frontend Dev Server
Write-Host '[2/2] Launching Frontend Dev Server on Port 5173...' -ForegroundColor Yellow
$frontendDir = Join-Path $RootDir 'frontend'
$frontendCommand = 'cd ' + $frontendDir + '; npm run dev'
Start-Process powershell -ArgumentList '-NoExit', '-Command', $frontendCommand

# Done
Write-Host ''
Write-Host 'Platform launched!' -ForegroundColor Green
Write-Host '==========================================================' -ForegroundColor Green
Write-Host 'Frontend: http://localhost:5173/' -ForegroundColor White
Write-Host 'Backend Swagger: http://localhost:8002/docs' -ForegroundColor White
Write-Host '==========================================================' -ForegroundColor Green
Write-Host 'Close the spawned windows to stop the servers.' -ForegroundColor Gray