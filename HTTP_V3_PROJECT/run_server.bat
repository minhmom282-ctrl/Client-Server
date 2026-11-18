@echo off
title HTTP Server Management - Group 6
chcp 65001 > nul
cd /d "%~dp0"

if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" main_server.py
    goto end
)

python main_server.py
if errorlevel 1 (
    echo [LOI] Khong tim thay Python.
    pause
)

:end
