@echo off
cd /d "%~dp0"

:: Matar instancias anteriores de Python que puedan estar usando el puerto 5000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":5000.*LISTENING"') do taskkill /PID %%a /F >nul 2>&1

:: Detectar Python: intentar "python", luego "py" (Python Launcher)
set PYTHON_CMD=
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
) else (
    py --version >nul 2>&1
    if %errorlevel% equ 0 (
        set PYTHON_CMD=py
    )
)

if "%PYTHON_CMD%"=="" (
    echo.
    echo ============================================
    echo  ERROR: No se encontro Python instalado.
    echo ============================================
    echo.
    echo  Opcion 1: Descarga Python desde https://www.python.org/downloads/
    echo             y marca "Add Python to PATH" durante la instalacion.
    echo.
    echo  Opcion 2: Si ya lo instalaste, reinicia la PC para que se actualice el PATH.
    echo.
    pause
    exit /b 1
)

echo Usando: %PYTHON_CMD%
%PYTHON_CMD% transmitir_web.py
pause
