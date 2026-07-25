# Resolve root directory from script location
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Split-Path -Parent $ScriptDir

Write-Host "Starting Infrastructure (Docker)..." -ForegroundColor Cyan
Set-Location -Path $RootDir
docker-compose -f docker-compose.dev.yml up -d

Write-Host "Starting Backend Service..." -ForegroundColor Cyan
$backendDir = Join-Path $RootDir "backend"
$backendCommand = 'cd "' + $backendDir + '"; .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --reload --port 8002'
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand

Write-Host "Starting AI Worker..." -ForegroundColor Cyan
$workerCommand = 'cd "' + $RootDir + '"; $env:PYTHONPATH="."; .\backend\.venv\Scripts\python.exe -m ai.worker.main'
Start-Process powershell -ArgumentList "-NoExit", "-Command", $workerCommand

Write-Host "Starting Frontend..." -ForegroundColor Cyan
$frontendDir = Join-Path $RootDir "frontend"
$frontendCommand = 'cd "' + $frontendDir + '"; npm run dev'
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCommand

Write-Host "Full System is starting up in separate windows!" -ForegroundColor Green
