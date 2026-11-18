@echo off
title HTTP Server CLI - Group 6
chcp 65001 > nul
cd /d "%~dp0"
python main_server.py --cli
if errorlevel 1 (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" main_server.py --cli
)
pause
