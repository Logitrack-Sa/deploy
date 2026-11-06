-- Script de inicialización automática de bases de datos para MySQL en Docker
-- Se ejecuta únicamente en la primera creación del volumen de datos

CREATE DATABASE IF NOT EXISTS `security_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS `courier_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS `logitrack` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS `shipment_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Crear y autorizar usuarios dedicados
CREATE USER IF NOT EXISTS 'logitrack'@'%' IDENTIFIED BY 'logitrack-dev';
GRANT ALL PRIVILEGES ON `logitrack`.* TO 'logitrack'@'%';
GRANT ALL PRIVILEGES ON `shipment_db`.* TO 'logitrack'@'%';

CREATE USER IF NOT EXISTS 'security_user'@'%' IDENTIFIED BY 'security_password';
GRANT ALL PRIVILEGES ON `security_db`.* TO 'security_user'@'%';

-- Asegurar permisos de root desde cualquier contenedor de la red Docker
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%' WITH GRANT OPTION;

FLUSH PRIVILEGES;
