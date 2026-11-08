@echo off
title Estadisticas de la notebook
echo Conectando el panel privado de la notebook...
echo Abrir en el navegador: http://127.0.0.1:13001/d/notebook-servidor
echo Dejar esta ventana abierta mientras se consulta el panel.
echo Cerrar esta ventana no detiene los servicios de la notebook.
ssh.exe -N -i "%USERPROFILE%\.ssh\notebook_vps_ed25519" -o "UserKnownHostsFile=%USERPROFILE%\Documents\ChatGPT\SERVIDOR_VPS\notebook-ssh\known_hosts" -o StrictHostKeyChecking=yes -o BatchMode=yes -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -L 127.0.0.1:13001:127.0.0.1:13001 alexxe@192.168.0.103
if errorlevel 1 (
  echo No se pudo abrir el tunel. Si el puerto 13001 ya esta ocupado, comprobar si el panel ya abre en el navegador.
  pause
)
