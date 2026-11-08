# Orquestador Maestro · LogiTrack Microservicios

Para la integración local actual del Sprint 4 usar la [guía de arranque y verificación](docs/SPRINT4-LOCAL.md). Incluye frontend, middleware, observabilidad y correo de prueba. Las instrucciones de cuatro contenedores que siguen describen la base anterior del repositorio.

Este directorio centraliza la infraestructura de contenedores para levantar todo el ecosistema de microservicios con un único comando en **Docker Desktop**.

## Topología de Contenedores

| Servicio | Contenedor | Puerto Host | Puerto Interno | Base de Datos |
|---|---|---|---|---|
| **MySQL 8.4** | `logitrack-mysql` | `3307` | `3306` | `security_db`, `courier_db`, `logitrack` |
| **`security-service`** | `logitrack-security-service` | `8083` | `8083` | `security_db` |
| **`courier-service`** | `logitrack-courier-service` | `8082` | `8082` | `courier_db` |
| **`shipment-service`** | `logitrack-shipment-service` | `8081` | `8081` | `logitrack` |

---

## Cómo Levantar Todo el Proyecto

### 1. Iniciar los contenedores
Desde esta carpeta (`deploy/`):

```bash
docker compose up --build -d
```

Docker Desktop construirá las imágenes empaquetando los `.jar` de cada microservicio y levantará los 4 contenedores en la red `logitrack_network`.

### 2. Ver en Docker Desktop
Abre la aplicación **Docker Desktop**. En la sección **Containers**, verás el grupo maestro llamado **`logitrack`** con los 4 contenedores funcionando juntos en verde.

### 3. Verificar estado de los servicios
```bash
curl http://localhost:8083/actuator/health
curl http://localhost:8082/actuator/health
curl http://localhost:8081/actuator/health
```

### 4. Detener todo el proyecto
```bash
docker compose down
```

*(Si deseas borrar también el volumen de la base de datos para empezar de cero, agrega `-v`: `docker compose down -v`).*

---

## Si modificas código Java en algún servicio

Dado que usamos el **Build Rápido** basado en los `.jar` de `target/`:
1. Ejecuta `./build-all.sh` (o `./mvnw package -DskipTests` en el servicio que modificaste).
2. Vuelve a ejecutar:
```bash
docker compose up --build -d
```

## Chatbot — Sprint 4 (#103)

Clonar `Logitrack-Sa/chatbot-service` junto a este repositorio, con JDK 21 o
superior, y preparar su JAR con `./mvnw -DskipTests package`. El Dockerfile de
chatbot consume ese artefacto y ejecuta JRE 21 fijado por digest como UID 10001.
También se incluye en `build-all.sh`, que mantiene el JDK 25 utilizado por los
otros servicios y genera bytecode Java 21 para chatbot.

El servicio expone `${HOST_CHATBOT_PORT:-8084}:8084`, se registra en Eureka y es
stateless. Límite del contenedor: 350M; heap máximo: 224m. Solo monta
`../certs/public.pem`, no la clave privada. Configurar en el entorno `AI_API_KEY`,
`AI_MODEL`, `JWT_ISSUER` y `JWT_KEY_ID` coherentes con security-service; las variables
`AI_BASE_URL` y `AI_COMPLETIONS_PATH` permiten elegir un proveedor compatible.
No utiliza MySQL ni credenciales de administrador. Los JWT del emisor deben incluir
las audiencias `chatbot-service`, `shipment-service` y `courier-service` para
consultas posteriores autorizadas por cada servicio de destino.

Config Server usa el perfil native ya previsto por Compose: se monta
`../config-repo:/config:ro` y se explicita `file:/config` como directorio de búsqueda.
Debe estar presente el nuevo `chatbot-service.properties` de la entrega #103.
Se configura `SERVER_ADDRESS=0.0.0.0` para que los clientes de la red Docker puedan
alcanzarlo. Prometheus ya incluye el target `chatbot-service:8084`.

En equipos limitados no ejecutar todo el stack ni `build-all.sh` para validar
esta entrega. La compilación del chatbot puede limitarse con
`JAVA_TOOL_OPTIONS="-Xmx256m -XX:ActiveProcessorCount=1" ./mvnw -DskipTests test-compile`.
Las pruebas de integración y el smoke del chatbot se ejecutan en su GitHub Actions.
La #104 añadirá las herramientas y el endpoint SSE productivo; no hay llamadas
a un proveedor de IA en los tests de la #103.
