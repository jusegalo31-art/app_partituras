@echo off
title ScoreLab - Partituras y Transpositor
cd /d "%~dp0"

echo ========================================================
echo   ScoreLab - Notacion Musical y Transpositor de PDFs
echo ========================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Python no se encuentra en el PATH estándar.
    echo Intentando ruta de usuario de Python...
    set "PY_PATH=%LOCALAPPDATA%\Python\bin\python.exe"
    if exist "%PY_PATH%" (
        echo Usando: %PY_PATH%
        "%PY_PATH%" -m streamlit run app.py
        goto end
    )
)

python -m streamlit run app.py

:end
pause
