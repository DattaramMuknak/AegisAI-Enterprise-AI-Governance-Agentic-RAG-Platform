-- Runs once on first MySQL container start (mounted to /docker-entrypoint-initdb.d)
CREATE DATABASE IF NOT EXISTS aegis_governance CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE DATABASE IF NOT EXISTS mlflow_tracking CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

GRANT ALL PRIVILEGES ON aegis_governance.* TO 'aegis'@'%';
GRANT ALL PRIVILEGES ON mlflow_tracking.* TO 'aegis'@'%';
FLUSH PRIVILEGES;
