#!/usr/bin/env bash
set -e

# Directorio raíz del proyecto
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export JAVA_HOME="/home/gonzalocar/.jdks/ms-25.0.4.1"

echo "=========================================================="
echo "Compilando y empaquetando microservicios con Java 25..."
echo "JAVA_HOME: $JAVA_HOME"
echo "=========================================================="

echo "[1/3] Empaquetando security-service..."
(cd "$PROJECT_ROOT/security-service" && ./mvnw package -DskipTests -B -q)

echo "[2/3] Empaquetando courier-service..."
(cd "$PROJECT_ROOT/courier-service" && ./mvnw package -DskipTests -B -q)

echo "[3/3] Empaquetando shipment-service..."
(cd "$PROJECT_ROOT/shipment-service" && ./mvnw package -DskipTests -B -q)

echo "=========================================================="
echo "¡Compilación completada exitosamente!"
echo "Ahora puedes ejecutar: docker compose up --build -d"
echo "=========================================================="
