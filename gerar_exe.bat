@echo off
title Gerar ALFRED.exe
cd /d "%~dp0"
call .venv\Scripts\activate.bat
pip install pyinstaller
pyinstaller --noconfirm --clean --windowed --name ALFRED --icon assets\alfred.ico --add-data "assets\alfred.ico;assets" --paths src --collect-all speech_recognition --collect-all edge_tts src\gui.py
if exist src\actions\.env copy /Y src\actions\.env dist\ALFRED\.env
echo.
echo Pronto: dist\ALFRED\ALFRED.exe
pause
