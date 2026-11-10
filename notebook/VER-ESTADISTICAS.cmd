@echo off
title Estadisticas de la notebook
if "%NOTEBOOK_SSH_TARGET%"=="" (
  echo Definir NOTEBOOK_SSH_TARGET con usuario@servidor antes de ejecutar.
  exit /b 1
)
if "%NOTEBOOK_SSH_KEY%"=="" (
  echo Definir NOTEBOOK_SSH_KEY con la ruta de la clave SSH.
  exit /b 1
)
if "%NOTEBOOK_KNOWN_HOSTS%"=="" (
  echo Definir NOTEBOOK_KNOWN_HOSTS con el archivo de hosts verificados.
  exit /b 1
)
echo Conectando el panel privado de la notebook...
echo Abrir en el navegador: http://127.0.0.1:13001/d/notebook-servidor
echo Dejar esta ventana abierta mientras se consulta el panel.
echo Cerrar esta ventana no detiene los servicios de la notebook.
ssh.exe -N -i "%NOTEBOOK_SSH_KEY%" -o "UserKnownHostsFile=%NOTEBOOK_KNOWN_HOSTS%" -o StrictHostKeyChecking=yes -o BatchMode=yes -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -L 127.0.0.1:13001:127.0.0.1:13001 "%NOTEBOOK_SSH_TARGET%"
if errorlevel 1 (
  echo No se pudo abrir el tunel. Si el puerto 13001 ya esta ocupado, comprobar si el panel ya abre en el navegador.
  pause
)
