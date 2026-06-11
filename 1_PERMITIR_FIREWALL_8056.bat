@echo off
title Permitir LigaPro F7 en Firewall
echo ==========================================================
echo   PERMITIR LIGAPRO F7 EN FIREWALL WINDOWS
echo ==========================================================
echo.
echo Este archivo intenta permitir el puerto 8056 en redes privadas.
echo Si Windows pide permisos de administrador, aceptalos.
echo.
netsh advfirewall firewall add rule name="LigaPro F7 V32 Puerto 8056" dir=in action=allow protocol=TCP localport=8056 profile=private
echo.
echo Regla agregada. Ahora ejecuta:
echo INICIAR_APP_V32_1_CELULAR_WIFI.bat
echo.
pause
