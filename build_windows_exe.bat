@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install Python 3.11 or newer from python.org.
  pause
  exit /b 1
)
py -m pip install -r requirements.txt
if errorlevel 1 goto :error
py -m PyInstaller --noconfirm --clean --onefile --windowed --name CSV-Scrubber app.py
if errorlevel 1 goto :error
echo.
echo Build complete: %CD%\dist\CSV-Scrubber.exe
pause
exit /b 0
:error
echo.
echo Build failed. Review the messages above.
pause
exit /b 1
