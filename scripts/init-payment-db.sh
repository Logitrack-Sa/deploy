#!/bin/sh
set -eu
[ -n "${PAYMENT_DB_PASSWORD:-}" ] || exit 0
case "$PAYMENT_DB_PASSWORD" in *[!a-zA-Z0-9_-]*) echo 'Formato de contraseña de pagos inválido' >&2; exit 1;; esac
[ "${#PAYMENT_DB_PASSWORD}" -ge 32 ] || { echo 'Contraseña de pagos demasiado corta' >&2; exit 1; }
MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysql --protocol=TCP -h"${MYSQL_HOST:-mysql}" -uroot <<SQL
CREATE DATABASE IF NOT EXISTS payment_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'payment_app'@'%' IDENTIFIED BY '${PAYMENT_DB_PASSWORD}';
GRANT ALL ON payment_db.* TO 'payment_app'@'%';
SQL
