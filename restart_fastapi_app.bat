@echo off
setlocal

echo ==============================================
echo QET FastAPI App Restart Script (Backend)
echo ==============================================

echo [1/3] Stopping any process listening on port 8000...
for /f "tokens=5" %%P in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
  echo   - Stopping PID %%P
  taskkill /F /PID %%P >nul 2>nul
)

echo [2/3] Stopping any process listening on port 8080...
for /f "tokens=5" %%P in ('netstat -ano ^| findstr :8080 ^| findstr LISTENING') do (
  echo   - Stopping PID %%P
  taskkill /F /PID %%P >nul 2>nul
)

echo [3/3] Starting FastAPI app on http://localhost:8000 ...
cd /d "%~dp0"
set PYTHONPATH=.
python -m uvicorn src.api.fastapi_app:app --host 127.0.0.1 --port 8000

endlocal
