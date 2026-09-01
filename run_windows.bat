@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python 3.11 or newer from python.org.
  pause
  exit /b 1
)
py -m pip install "rapidfuzz>=3.0,<4" "PySide6>=6.8,<7"
if errorlevel 1 (
  echo Could not install application dependencies.
  pause
  exit /b 1
)
py app.py
