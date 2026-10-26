@echo off
title ALFRED 1.0 - Interface
cd /d "%~dp0"
call .venv\Scripts\activate.bat
python src\gui.py
pause
