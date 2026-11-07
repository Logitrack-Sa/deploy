#!/usr/bin/env bash
set -e

# Directorio raíz del proyecto
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export JAVA_HOME="/home/gonzalocar/.jdks/ms-25.0.4.1"

echo "=========================================================="
echo "Compilando y empaquetando microservicios con Java 25..."
echo "JAVA_HOME: $JAVA_HOME"
echo "=========================================================="

echo "[1/4] Empaquetando security-service..."
(cd "$PROJECT_ROOT/security-service" && ./mvnw package -DskipTests -B -q)

echo "[2/4] Empaquetando courier-service..."
(cd "$PROJECT_ROOT/courier-service" && ./mvnw package -DskipTests -B -q)

echo "[3/4] Empaquetando shipment-service..."
(cd "$PROJECT_ROOT/shipment-service" && ./mvnw package -DskipTests -B -q)

echo "=========================================================="
echo "[4/4] Empaquetando chatbot-service (bytecode Java 21)..."
(cd "$PROJECT_ROOT/chatbot-service" && ./mvnw package -DskipTests -B -q)

echo "¡Compilación completada exitosamente!"
echo "Ahora puedes ejecutar: docker compose up --build -d"
echo "=========================================================="
