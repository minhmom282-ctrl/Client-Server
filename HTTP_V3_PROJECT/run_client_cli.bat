@echo off
title HTTP Client CLI - Group 6
chcp 65001 > nul
cd /d "%~dp0"
python main_client.py --cli
if errorlevel 1 (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" main_client.py --cli
)
pause
