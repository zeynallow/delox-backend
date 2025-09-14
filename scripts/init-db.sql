-- Initialize databases for each service
CREATE DATABASE auth_service;
CREATE DATABASE user_service;
CREATE DATABASE order_service;
CREATE DATABASE courier_service;
CREATE DATABASE notification_service;
CREATE DATABASE analytics_service;

-- Create users for each service (optional, for better security)
CREATE USER auth_user WITH PASSWORD 'auth_password';
CREATE USER user_user WITH PASSWORD 'user_password';
CREATE USER order_user WITH PASSWORD 'order_password';
CREATE USER courier_user WITH PASSWORD 'courier_password';
CREATE USER notification_user WITH PASSWORD 'notification_password';
CREATE USER analytics_user WITH PASSWORD 'analytics_password';

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE auth_service TO auth_user;
GRANT ALL PRIVILEGES ON DATABASE user_service TO user_user;
GRANT ALL PRIVILEGES ON DATABASE order_service TO order_user;
GRANT ALL PRIVILEGES ON DATABASE courier_service TO courier_user;
GRANT ALL PRIVILEGES ON DATABASE notification_service TO notification_user;
GRANT ALL PRIVILEGES ON DATABASE analytics_service TO analytics_user;

-- Enable UUID extension for all databases
\c auth_service;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

\c user_service;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

\c order_service;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

\c courier_service;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

\c notification_service;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

\c analytics_service;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
