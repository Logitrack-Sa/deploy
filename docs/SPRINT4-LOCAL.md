# Ejecutar la integración local del Sprint 4

Este entorno conserva el Sprint 3 y usa otra base de datos. No requiere Gmail para probar el registro: los mensajes quedan en Mailpit local. No contiene una clave de proveedor IA.

## Preparación

Los repositorios deben estar como carpetas hermanas: config-server, config-repo, eureka-server, security-service, courier-service, shipment-service, api-gateway, chatbot-service, logitrack-frontend y deploy. Para esta integración se requieren las ramas locales señaladas en el informe del frontend; todavía no están publicadas.

Compilar cada servicio Java con su mvnw verify usando JDK 25. Los Dockerfile Java empaquetan los JAR de target; los contextos Docker excluyen archivos privados y envían únicamente el artefacto necesario. El frontend requiere Node.js 22.12 o posterior y se compila dentro del Dockerfile.

Desde deploy:

```sh
python scripts/prepare_local.py
docker compose --env-file target/sprint4/runtime.env -f docker-compose.yml -f docker-compose.local.yml -p logitrack-sprint4-local config --quiet
docker compose --env-file target/sprint4/runtime.env -f docker-compose.yml -f docker-compose.local.yml -p logitrack-sprint4-local up -d --build --wait --wait-timeout 420
python scripts/verify_local.py
```

prepare_local.py genera una contraseña ADMIN y claves RSA exclusivas de esta instalación. Si runtime.env ya existe, lo conserva sin reemplazar credenciales. Nunca versionar ni compartir ese archivo o private.pem. Las credenciales del login están en SECURITY_ADMIN_EMAIL y SECURITY_ADMIN_PASSWORD de ese archivo privado.

## Direcciones

| Pantalla o API | URL local |
|---|---|
| Aplicación web | http://localhost:3000 |
| Gateway | http://localhost:8086 |
| Eureka | http://localhost:9065 |
| Config Server | http://localhost:9088 |
| Correos de prueba (Mailpit) | http://localhost:8025 |
| Grafana | http://localhost:3001 |
| Prometheus | http://localhost:9090 |
| RabbitMQ | http://localhost:15673 |

El puerto 8086 evita el conflicto de esta computadora con Apache en 8080. FRONTEND_API_GATEWAY_URL y HOST_GATEWAY_PORT deben apuntar al mismo destino público. Cambiar una variable NEXT_PUBLIC requiere reconstruir frontend.

## Chatbot

El overlay local deja chatbot-service en el perfil ai. Para activarlo se necesitan AI_API_KEY y AI_MODEL reales en runtime.env, con AI_BASE_URL/AI_COMPLETIONS_PATH si el proveedor lo requiere. No usar el token de Copilot de GitHub como clave del modelo.

```sh
docker compose --env-file target/sprint4/runtime.env -f docker-compose.yml -f docker-compose.local.yml -p logitrack-sprint4-local --profile ai up -d --build chatbot-service
```

Sin esas variables no se acredita una conversación IA real. Las pruebas Java usan un proveedor simulado local para validar el transporte y las herramientas, sin consumo de un modelo de pago.

## Estado del contrato

Courier todavía usa ACTIVO/INACTIVO: mantener FRONTEND_COURIER_STATUS_MODEL=legacy. La herramienta del chatbot que solicita AVAILABLE requiere la evolución pendiente de Courier. La cancelación CLIENTE sigue desactivada hasta que el backend autorice al propietario.

Las pruebas HTTP crean datos sintéticos con correos @example.test. Verifican backend real y correo SMTP capturado, no entrega Gmail. No borran datos previos. verification.json y sources.json se guardan en target/sprint4 y no contienen tokens ni contraseñas.

Para detener este entorno conservando sus datos, usar la misma combinación de archivos y proyecto con stop. No añadir down -v para una instalación con datos que se quieran conservar. El Sprint 3 quedó detenido durante la prueba para ahorrar memoria; sus volúmenes no se eliminaron.
