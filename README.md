# Orquestador Maestro · LogiTrack Microservicios

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
