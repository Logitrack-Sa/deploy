#!/usr/bin/env bash
set -eu
mysql --protocol=socket -uroot -p"$MYSQL_ROOT_PASSWORD" <<SQL
CREATE USER IF NOT EXISTS 'security_app'@'%' IDENTIFIED BY '${SECURITY_DB_PASSWORD}';
CREATE USER IF NOT EXISTS 'courier_app'@'%' IDENTIFIED BY '${COURIER_DB_PASSWORD}';
CREATE USER IF NOT EXISTS 'shipment_app'@'%' IDENTIFIED BY '${SHIPMENT_DB_PASSWORD}';
GRANT ALL ON security_db.* TO 'security_app'@'%';
GRANT ALL ON courier_db.* TO 'courier_app'@'%';
GRANT ALL ON logitrack.* TO 'shipment_app'@'%';
GRANT ALL ON shipment_db.* TO 'shipment_app'@'%';
SQL
