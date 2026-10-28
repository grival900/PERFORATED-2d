@echo off
rem Installs pygame-ce if needed, then runs the game from source.
cd /d "%~dp0"
python -c "import pygame" 2>nul || python -m pip install -q pygame-ce
python main.py
if errorlevel 1 pause
