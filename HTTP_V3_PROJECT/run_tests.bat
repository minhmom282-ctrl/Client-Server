@echo off
title Comprehensive Test Suite - Group 6
chcp 65001 > nul
cd /d "%~dp0"
echo ========================================================
echo   CHAY KIEM THU TU DONG 10 KICH BAN - NHOM 6
echo ========================================================
python tests\test_all_cases.py
if errorlevel 1 (
    echo.
    echo Thu lai voi duong dan Python mac dinh...
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" tests\test_all_cases.py
)
pause
