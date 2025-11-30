

CREATE DATABASE IF NOT EXISTS db_paquexpress;
USE db_paquexpress;

-- 1. Tabla de Usuarios (Con Rol)
CREATE TABLE P9_users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL, -- Se usará MD5 según tu esquema
    full_name VARCHAR(100) NOT NULL,
    role ENUM('ADMIN', 'WORKER') NOT NULL DEFAULT 'WORKER', -- NUEVO CAMPO
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insertar datos de prueba
-- Admin: admin / admin123
-- Trabajador: agente1 / paquexpress123
INSERT INTO P9_users (username, password_hash, full_name, role) VALUES
('admin', MD5('admin123'), 'Administrador General', 'ADMIN'),
('agente1', MD5('paquexpress123'), 'Agente Juan Pérez', 'WORKER'),
('agente2', MD5('paquexpress123'), 'Agente Maria Lopez', 'WORKER');

-- 2. Tabla de Paquetes
CREATE TABLE P9_packages (
    package_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT 'Agente asignado',
    destination_address VARCHAR(255) NOT NULL,
    description VARCHAR(255) COMMENT 'Detalle del paquete',
    delivery_status ENUM('PENDIENTE', 'ENTREGADO', 'FALLIDO') DEFAULT 'PENDIENTE',
    FOREIGN KEY (user_id) REFERENCES P9_users(user_id)
);

-- Paquetes de prueba
INSERT INTO P9_packages (user_id, destination_address, description) VALUES
(2, 'Av. Pie de la Cuesta No. 2501, Querétaro', 'Caja Grande'),
(2, 'Calle 5 de Febrero, Centro, Querétaro', 'Sobre Documentos');

-- 3. Tabla de Entregas (Evidencia)
CREATE TABLE P9_deliveries (
    delivery_id INT AUTO_INCREMENT PRIMARY KEY,
    package_id INT NOT NULL UNIQUE,
    agent_id INT NOT NULL,
    latitude DECIMAL(10, 8) NOT NULL,
    longitude DECIMAL(11, 8) NOT NULL,
    location_address VARCHAR(255),
    photo_path VARCHAR(255) NOT NULL,
    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (package_id) REFERENCES P9_packages(package_id),
    FOREIGN KEY (agent_id) REFERENCES P9_users(user_id)
);