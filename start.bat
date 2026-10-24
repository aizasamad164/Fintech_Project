@echo off
REM ============================================================
REM  StockSense - start backend + frontend, then open the app.
REM  Put this file in the Fintech_Project folder and double-click.
REM  Close the two windows it opens to stop the app.
REM ============================================================
setlocal
set "ROOT=%~dp0"

if not exist "%ROOT%backend\venv\Scripts\activate.bat" (
  echo.
  echo  Backend setup not found: backend\venv is missing.
  echo  First-time setup, in the backend folder:
  echo    python -m venv venv
  echo    venv\Scripts\activate
  echo    pip install -r requirements.txt
  echo.
  pause
  exit /b 1
)

if not exist "%ROOT%frontend\node_modules" (
  echo.
  echo  Frontend packages not installed. Running npm install once...
  pushd "%ROOT%frontend"
  call npm install
  popd
)

echo Starting backend on http://localhost:8000 ...
start "StockSense backend" cmd /k "cd /d "%ROOT%backend" && call venv\Scripts\activate.bat && uvicorn app.main:app --reload --port 8000"

echo Starting frontend on http://localhost:5173 ...
start "StockSense frontend" cmd /k "cd /d "%ROOT%frontend" && npm run dev"

echo Opening the app in your browser in a few seconds...
timeout /t 8 /nobreak >nul
start "" http://localhost:5173

endlocal
