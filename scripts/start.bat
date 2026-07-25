@echo off
set "SCRIPT_DIR=%~dp0"
set "ROOT_DIR=%SCRIPT_DIR%.."

cd /d "%ROOT_DIR%"

echo Starting Infrastructure (Docker)...
docker-compose -f docker-compose.dev.yml up -d

echo Starting Backend Service...
start cmd /k "cd backend && call .venv\Scripts\activate.bat && uvicorn app.main:app --reload --port 8002"

echo Starting AI Worker...
start cmd /k "set PYTHONPATH=. && backend\.venv\Scripts\python.exe -m ai.worker.main"

echo Starting Frontend...
start cmd /k "cd frontend && npm run dev"

echo Full System is starting up in separate windows!
