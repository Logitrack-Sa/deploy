#!/usr/bin/env bash
# Copia consistente de las bases y configuración. No detiene las aplicaciones.
set -euo pipefail
umask 077
cd /srv/apps/logitrack
exec 9>backups/.backup.lock
flock -n 9 || exit 0
stamp=$(date -u +%Y%m%dT%H%M%SZ)
destination="backups/daily/$stamp"
mkdir -p "$destination"
trap 'rm -f "$destination/mysql.sql.gz.partial"' EXIT
docker compose exec -T mysql sh -c '
  export MYSQL_PWD="$MYSQL_ROOT_PASSWORD"
  databases="security_db courier_db logitrack shipment_db"
  if mysql -uroot --batch --skip-column-names -e "SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME=0x7061796d656e745f6462" | grep -qx payment_db; then
    databases="$databases payment_db"
  fi
  exec mysqldump -uroot --single-transaction --routines --triggers --events \
    --set-gtid-purged=OFF --no-tablespaces \
    --databases $databases
' | gzip > "$destination/mysql.sql.gz.partial"
gzip -t "$destination/mysql.sql.gz.partial"
mv "$destination/mysql.sql.gz.partial" "$destination/mysql.sql.gz"
tar -czf "$destination/config.tar.gz" -- .env compose.yaml config secrets \
  mysql-init healthcheck docker images.json sources.json logitrack.caddy \
  README.md backup.sh update_public_url.py verify.py node-exporter.json prometheus-node.yml
(cd "$destination" && sha256sum mysql.sql.gz config.tar.gz > SHA256SUMS)
printf 'Backup terminado: %s\n' "$destination"
