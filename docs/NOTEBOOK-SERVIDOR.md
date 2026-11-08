# Logitrack en la notebook

Prometheus consulta Gateway, Security, Courier y Shipment dentro de la red
privada. En los tres backends se activa `logitrack.metrics.anonymous-enabled`
solo para `GET /actuator/prometheus`; su valor por defecto es `false`.
Las rutas de negocio conservan JWT/RBAC. Caddy no publica `/actuator/`.
El chatbot sin configurar se omite de esta monitorización.

Instalación: `/srv/apps/logitrack`, proyecto Compose `logitrack-notebook`.
Acceso LAN: <http://192.168.0.103/logitrack/>. Para el enlace HTTPS actual,
ejecutar `vps-url` en el servidor y agregar `/logitrack/`.

El servidor ejecuta frontend, Gateway, Eureka, Config Server, Security, Courier,
Shipment, MySQL, Redis, RabbitMQ, Grafana, Prometheus, Mailpit y Node Exporter: 14 contenedores. Las bases,
colas, caché y paneles internos no se publican en Internet. Caddy conserva el
sitio original y `/demo/`. La PC Windows ya no necesita ejecutar esos servicios.
Todos arrancan automáticamente con Docker y tienen límites de memoria; MySQL
dispone de 1 GiB y Security/Shipment de 768 MiB cada uno.

## Operación por SSH

```bash
cd /srv/apps/logitrack
docker compose ps
docker compose logs --tail=50 shipment-service
docker compose up -d --wait --wait-timeout 420
./backup.sh
```

Las aplicaciones son una copia de las versiones locales del 8 de noviembre de 2026;
no se publicaron cambios de Sprint 4 en GitHub ni Docker Hub. `images.json`
identifica sus IDs, y `sources.json` las revisiones de origen. La configuración
de Config Server es una copia local fijada en `config/`; no descarga cambios
de los compañeros automáticamente.

`.env` y `secrets/` contienen credenciales y claves privadas; se conservan solo
en el servidor y en las copias privadas. No adjuntarlos al aula ni al repositorio.
Las cuentas y las claves JWT existentes se migraron. Cada backend utiliza una
cuenta de MySQL limitada a su base. Los certificados y passwords no se muestran
en esta guía.

## Paneles internos

Para abrirlos desde Windows, dejar esta sesión SSH en ejecución:

```powershell
ssh -i C:\Users\Alexxe\.ssh\notebook_vps_ed25519 -o UserKnownHostsFile=C:\Users\Alexxe\Documents\ChatGPT\SERVIDOR_VPS\notebook-ssh\known_hosts -o StrictHostKeyChecking=yes -N -L 18065:127.0.0.1:18065 -L 13001:127.0.0.1:13001 -L 19090:127.0.0.1:19090 -L 18025:127.0.0.1:18025 alexxe@192.168.0.103
```

Eureka: `http://localhost:18065/`; Grafana: `http://localhost:13001/`;
Prometheus: `http://localhost:19090/`; correo de pruebas: `http://localhost:18025/`.
Cerrar SSH cierra estos accesos, sin detener los servicios.

### Estadísticas de la notebook

Panel: <http://127.0.0.1:13001/d/notebook-servidor>. Se consulta desde esta PC
mediante el túnel SSH; no es un enlace público. Para volver a conectar después
de reiniciar Windows, ejecutar `deploy/notebook/VER-ESTADISTICAS.cmd` y mantener
esa ventana abierta. Usar la cuenta de Grafana existente; no se desactivó el login.

Incluye CPU, RAM, swap, temperaturas del procesador y SSD NVMe, disco disponible,
actividad del disco, carga y tiempo encendida. Las mediciones se recogen cada
15 segundos; su historial comienza con la instalación y se conserva hasta 2 días.
No hay sensor de RPM de ventilador disponible. Los datos corresponden a Ubuntu
en la notebook, no a la PC Windows ni a un contenedor aislado.

Node Exporter usa la imagen oficial v1.12.1 fijada por digest, sin puertos
publicados, con usuario sin privilegios y montaje de lectura del host. Solo
se activaron los colectores necesarios; no se instaló un agente en Windows.
Referencia: <https://github.com/prometheus/node_exporter>.

## Respaldo y recuperación

`backups/` conserva el estado previo del proxy, imágenes verificadas por SHA256,
dump inicial de las cuatro bases y archivos de Grafana/Prometheus. La migración
inicial verificó 2 usuarios, 1 repartidor, 3 clientes y 3 envíos antes de crear
datos sintéticos para las pruebas HTTP.

`backup.sh` genera dumps consistentes y configuración privada en `backups/daily/`.
Se ejecuta diariamente a las 03:35 mediante el crontab de `alexxe`.
No borra copias automáticamente. Los backups están en el mismo disco: copiarlos
a otro equipo de forma privada para cubrir averías del servidor. Para restaurar,
detener primero los servicios que escriben y revisar el destino antes de cargar
el SQL. No ejecutar `docker compose down -v`: borraría los datos persistentes.
Los volúmenes de la PC se conservaron como punto de recuperación, con las
escrituras detenidas para evitar dos instalaciones divergentes.

## Límites actuales

La notebook necesita alimentación y red. La IP es DHCP. El enlace de Cloudflare
es temporal y cambia si se reinicia el túnel; ejecutar
`python3 /srv/apps/logitrack/update_public_url.py` para actualizar los correos
y los orígenes permitidos del Gateway. No es necesario reconstruir frontend
porque usa rutas relativas.

El chatbot no se inició: faltan `AI_API_KEY` y `AI_MODEL`. Además, el Quick Tunnel
actual no admite SSE; para el chat con streaming hace falta otro método de
publicación o un túnel permanente. Mailpit captura los correos de prueba;
todavía no se envían a casillas reales. Estos límites no se presentan como
funciones terminadas.
