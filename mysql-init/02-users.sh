#!/bin/sh
set -eu
for value in "${SECURITY_DB_PASSWORD:-}" "${COURIER_DB_PASSWORD:-}" "${SHIPMENT_DB_PASSWORD:-}" "${PAYMENT_DB_PASSWORD:-}"; do
    case "$value" in ''|*[!a-zA-Z0-9_-]*) echo 'Contraseña de base de datos ausente o con formato inválido' >&2; exit 1;; esac
    [ "${#value}" -ge 32 ] || { echo 'Usar contraseñas generadas de al menos 32 caracteres' >&2; exit 1; }
done
MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql --protocol=socket -uroot <<SQL
CREATE USER IF NOT EXISTS 'security_app'@'%' IDENTIFIED BY '${SECURITY_DB_PASSWORD}';
CREATE USER IF NOT EXISTS 'courier_app'@'%' IDENTIFIED BY '${COURIER_DB_PASSWORD}';
CREATE USER IF NOT EXISTS 'shipment_app'@'%' IDENTIFIED BY '${SHIPMENT_DB_PASSWORD}';
CREATE USER IF NOT EXISTS 'payment_app'@'%' IDENTIFIED BY '${PAYMENT_DB_PASSWORD}';
GRANT ALL ON security_db.* TO 'security_app'@'%';
GRANT ALL ON courier_db.* TO 'courier_app'@'%';
GRANT ALL ON shipment_db.* TO 'shipment_app'@'%';
GRANT ALL ON payment_db.* TO 'payment_app'@'%';
SQL
