# Ejecutar LogiTrack

Requiere Docker Engine o Docker Desktop con Compose, Git, Python 3 y OpenSSL.
Los servicios Java se compilan dentro de las imágenes con Java 25; para probarlos
fuera de Docker se necesita un JDK 25 en `JAVA_HOME` o en el `PATH`.

Clonar los once repositorios de la organización como carpetas hermanas: `deploy`,
`config-repo`, `config-server`, `eureka-server`, `api-gateway`, `security-service`,
`courier-service`, `shipment-service`, `chatbot-service`, `payment-service` y
`logitrack-frontend`. Usar las revisiones de `main` de la entrega integrada.

Desde la carpeta `deploy`:

```bash
python scripts/prepare_local.py
docker compose --env-file target/local/runtime.env -f docker-compose.yml -f docker-compose.local.yml up -d --build --wait --wait-timeout 600
```

El generador crea contraseñas distintas y claves RSA propias. Si el entorno ya
existe, lo conserva. `runtime.env` y `certs` quedan fuera de Git. El directorio
privado protege los archivos en Windows mediante ACL y en Linux mediante permisos.
El usuario inicial es `SECURITY_ADMIN_USERNAME`; su contraseña está en
`SECURITY_ADMIN_PASSWORD` del archivo generado. No hay una contraseña universal.

| Acceso | Dirección local por defecto |
|---|---|
| Sitio | http://localhost:3000 |
| API Gateway | http://localhost:8086 |
| Eureka | http://localhost:9065 |
| Config Server | http://localhost:9088 |
| Correos de pruebas, incluido recuperar contraseña | http://localhost:8025 |
| Grafana | http://localhost:3001 |
| Prometheus | http://localhost:9090 |

Los puertos se pueden cambiar en `runtime.env`. Si cambia el puerto del sitio,
actualizar también `LOGITRACK_PUBLIC_URL` y `CORS_ALLOWED_ORIGINS`. Cambiar la URL
del Gateway requiere ajustar `FRONTEND_API_GATEWAY_URL` y reconstruir el frontend.

Cada servicio de negocio tiene su propio esquema y usuario MySQL. La inicialización
SQL se aplica a volúmenes vacíos; modificar el `.env` no cambia las contraseñas de
una base existente. Conservar el entorno con su volumen y usar migraciones para
actualizaciones. `docker compose down` conserva los volúmenes. No agregar `-v`
cuando existan datos que deban conservarse.

## IA y pagos

El entorno local captura el correo en Mailpit. La captura no requiere una
contraseña SMTP inventada. Para correo externo se usa la configuración del proveedor
y se ejecuta Compose sin la sobreescritura local de Mailpit.

El chatbot es opcional en desarrollo: configurar `AI_API_KEY`, `AI_MODEL`,
`AI_BASE_URL` y `AI_COMPLETIONS_PATH`, y agregar `--profile ai` al comando.
Para Gemini, la compatibilidad de firmas se habilita con `GEMINI_PROXY_ENABLED=true`
y `AI_BASE_URL=http://127.0.0.1:18089`, `AI_COMPLETIONS_PATH=/chat/completions`.
El origen externo del proxy se puede configurar con `GEMINI_PROXY_TARGET_URL`.

Los pagos permanecen deshabilitados sin credenciales. Para una prueba, configurar
un Access Token de prueba, `MERCADOPAGO_SANDBOX=true`, la firma del Webhook,
`PAYMENTS_ENABLED=true` y `FRONTEND_PAYMENTS_ENABLED=true`, y reconstruir el frontend.
El Webhook necesita una URL HTTPS accesible. El entorno privado del servidor y sus
credenciales de producción se administran por separado.

## Comprobar y detener

```bash
docker compose --env-file target/local/runtime.env -f docker-compose.yml -f docker-compose.local.yml ps
docker compose --env-file target/local/runtime.env -f docker-compose.yml -f docker-compose.local.yml logs --tail 100
docker compose --env-file target/local/runtime.env -f docker-compose.yml -f docker-compose.local.yml stop
```

Los perfiles `dev`/`prod` seleccionan el entorno; `discovery` habilita el registro
en Eureka y `observability` las métricas. Los documentos de entregas anteriores
se conservan como historial y no son la guía de arranque actual.
