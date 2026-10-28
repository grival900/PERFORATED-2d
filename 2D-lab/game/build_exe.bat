@echo off
rem Builds a single-file Windows executable: dist\PERFORATED.exe
cd /d "%~dp0"
python -m pip install -q pygame-ce pyinstaller || goto :err
python -m PyInstaller --noconfirm --clean --onefile --windowed --name PERFORATED ^
  --add-data "assets;assets" main.py || goto :err
echo.
echo Done: %~dp0dist\PERFORATED.exe
exit /b 0
:err
echo Build failed.
exit /b 1
