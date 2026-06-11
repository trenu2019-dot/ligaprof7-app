@echo off
title LigaPro F7 V32.1 - Celular Red WiFi
cd /d "%~dp0"
cls
echo ==========================================================
echo   LIGAPRO F7 V32.1 - HOTFIX CELULAR RED WIFI
echo ==========================================================
echo.
echo Esta version escucha en toda la red WiFi.
echo.
echo En computadora:
echo http://127.0.0.1:8056
echo.
echo En celular usa la IP IPv4 de esta computadora:
echo.
ipconfig | findstr /i "IPv4"
echo.
echo Ejemplo:
echo http://192.168.1.75:8056
echo.
echo IMPORTANTE:
echo Si Windows pregunta permisos de red, presiona PERMITIR.
echo Debe ser red PRIVADA, no publica.
echo.
echo Usuarios:
echo admin / 2026
echo.
where py >nul 2>nul
if %errorlevel%==0 (
  start "" http://127.0.0.1:8056
  start "" http://127.0.0.1:8056/celular
  set PORT=8056
  py -3 backend\server.py
  pause
  exit /b
)
where python >nul 2>nul
if %errorlevel%==0 (
  start "" http://127.0.0.1:8056
  start "" http://127.0.0.1:8056/celular
  set PORT=8056
  python backend\server.py
  pause
  exit /b
)
echo ERROR: No se encontro Python.
pause
