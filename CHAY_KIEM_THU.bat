@echo off
title Kiem Thu Tu Dong 10 Kich Ban - Group 6
chcp 65001 > nul
cd /d "%~dp0\HTTP_V3_PROJECT"
python tests\test_all_cases.py
if errorlevel 1 (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" tests\test_all_cases.py
)
pause
