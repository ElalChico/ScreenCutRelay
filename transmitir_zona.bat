@echo off
cd /d "%~dp0"

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
%PYTHON_CMD% transmitir_zona.py
pause
