@echo off
title HTTP Client Register - Group 6
chcp 65001 > nul
cd /d "%~dp0\HTTP_V3_PROJECT"

:: Uu tien su dung Python 3.12 da cai dat
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" main_client.py
    goto end
)

:: Thu goi python tu bien moi truong
python main_client.py
if errorlevel 1 (
    echo.
    echo [LOI] Khong tim thay Python. Vui long kiem tra lai cai dat Python!
    pause
)

:end
