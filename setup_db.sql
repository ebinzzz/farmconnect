-- Run this in MySQL before starting the project
-- mysql -u root -p < setup_db.sql

CREATE DATABASE IF NOT EXISTS farmconnect_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'farmconnect_user'@'localhost' IDENTIFIED BY 'StrongPassword123!';
GRANT ALL PRIVILEGES ON farmconnect_db.* TO 'farmconnect_user'@'localhost';
FLUSH PRIVILEGES;

SELECT 'FarmConnect database created successfully!' AS status;
