@echo off
echo.
echo ========================================================
echo Dando permisos en el Firewall de Windows para Scrcpy Web
echo (Si te pide permisos de Administrador, dile que SI)
echo ========================================================
echo.

net session >nul 2>&1
if %errorLevel% == 0 (
    netsh advfirewall firewall add rule name="Scrcpy Web" dir=in action=allow protocol=TCP localport=5000
    echo.
    echo ¡Listo! El puerto 5000 ha sido abierto en el Firewall.
    echo Ya puedes intentar entrar desde la otra PC.
    echo.
    pause
) else (
    echo ERROR: Necesitas ejecutar este archivo como Administrador.
    echo Haz clic derecho sobre "abrir_puerto_firewall.bat" y selecciona "Ejecutar como administrador".
    echo.
    pause
)
