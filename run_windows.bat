@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python 3.11 or newer from python.org.
  pause
  exit /b 1
)
py -m pip install rapidfuzz
if errorlevel 1 (
  echo Could not install RapidFuzz.
  pause
  exit /b 1
)
py app.py
