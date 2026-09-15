@echo off
setlocal
cd /d %~dp0
where py >nul 2>nul
if %errorlevel%==0 (
  set PY=py -3
) else (
  where python >nul 2>nul
  if not %errorlevel%==0 (
    echo Python 3.11+ is required. Install Python from python.org and check "Add python.exe to PATH".
    pause
    exit /b 1
  )
  set PY=python
)
if not exist .venv %PY% -m venv .venv
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul
python -m pip install -r backend\requirements.txt
REM Needed only to build the Windows Native Messaging bridge from source.
python -m pip install pyinstaller
python scripts\preflight.py
if not %errorlevel%==0 (
  echo Preflight failed. Review the messages above.
  pause
  exit /b 1
)
python desktop\app.py
endlocal
