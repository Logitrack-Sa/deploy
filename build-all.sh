#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if ! command -v java >/dev/null 2>&1; then
    echo 'Configurar JAVA_HOME o instalar Java 25 y agregarlo al PATH.' >&2
    exit 1
fi
for service in config-server eureka-server security-service courier-service shipment-service api-gateway chatbot-service payment-service; do
    echo "Empaquetando $service..."
    (cd "$PROJECT_ROOT/$service" && bash ./mvnw --batch-mode --no-transfer-progress package "$@")
done
