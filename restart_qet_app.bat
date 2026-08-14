@echo off
setlocal

echo ==============================================
echo QET App Restart Script
echo ==============================================

cd /d "%~dp0"

echo [1/4] Stopping any process listening on port 8501...
for /f "tokens=5" %%P in ('netstat -ano ^| findstr :8501 ^| findstr LISTENING') do (
  echo   - Stopping PID %%P
  taskkill /F /PID %%P >nul 2>nul
)

echo [2/4] Clearing Python cache (__pycache__ and *.pyc)...
for /d /r %%D in (__pycache__) do rd /s /q "%%D" 2>nul
del /s /q "*.pyc" 2>nul

echo [3/4] Verifying Python environment...
if exist ".venv\Scripts\python.exe" (
  set "PY_EXE=.venv\Scripts\python.exe"
  echo   - Using virtual environment: .venv\Scripts\python.exe
) else (
  set "PY_EXE=python"
  echo   - .venv not found, using system python from PATH
)

echo [4/4] Starting Streamlit app on http://localhost:8501 ...
%PY_EXE% -m streamlit run app.py

endlocal
