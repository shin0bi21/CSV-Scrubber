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
for /f "delims=" %%I in ('py -c "import customtkinter, pathlib; print(pathlib.Path(customtkinter.__file__).parent)"') do set "CUSTOMTKINTER_PATH=%%I"
if not defined CUSTOMTKINTER_PATH goto :error
py -m PyInstaller --noconfirm --clean --onedir --windowed --name CSV-Scrubber --add-data "%CUSTOMTKINTER_PATH%;customtkinter" app.py
if errorlevel 1 goto :error
echo.
echo Build complete: %CD%\dist\CSV-Scrubber\CSV-Scrubber.exe
pause
exit /b 0
:error
echo.
echo Build failed. Review the messages above.
pause
exit /b 1
