@echo off
setlocal
cd /d "%~dp0"

echo ==========================================
echo   Building METOO Bluetooth Monitor
echo ==========================================

if not exist ".venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found.
    echo Create it with: py -3.12 -m venv .venv
    pause
    exit /b 1
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

pyinstaller --noconfirm --clean --onefile --windowed ^
  --name "METOO-Bluetooth-Monitor" ^
  --collect-all winrt ^
  --collect-all winotify ^
  --collect-all pystray ^
  app.py

if errorlevel 1 (
    echo.
    echo BUILD FAILED. Check the messages above.
    pause
    exit /b 1
)

echo.
echo BUILD COMPLETE:
echo dist\METOO-Bluetooth-Monitor.exe
pause
