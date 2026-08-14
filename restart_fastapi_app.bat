@echo off
setlocal

echo ==============================================
echo QET FastAPI App Restart Script (Port 8080)
echo ==============================================

echo [1/3] Stopping any process on port 8000 and 8080...
for /f "tokens=5" %%P in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
  echo   - Stopping PID %%P
  taskkill /F /PID %%P >nul 2>nul
)

for /f "tokens=5" %%P in ('netstat -ano ^| findstr :8080 ^| findstr LISTENING') do (
  echo   - Stopping PID %%P
  taskkill /F /PID %%P >nul 2>nul
)

echo [2/3] Setting environment...
cd /d "%~dp0"
set PYTHONPATH=.
set QET_ENABLE_REQUIREMENT_CATEGORIZATION=true

echo [3/3] Starting FastAPI app on http://127.0.0.1:8080 ...
python -m uvicorn src.api.fastapi_app:app --host 127.0.0.1 --port 8080 --reload

endlocal
