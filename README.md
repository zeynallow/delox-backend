# 🚚 Delox - SaaS Delivery Management System

A comprehensive multi-tenant delivery management platform built with Python microservices.

## 🏗️ Architecture

### Microservices
- **API Gateway** - Request routing, authentication, rate limiting
- **Auth Service** - JWT authentication, multi-tenant authorization
- **User Service** - User management, workspace management, RBAC
- **Order Service** - Order lifecycle, API integrations, webhooks
- **Courier Service** - Route optimization, GPS tracking, task assignment
- **Notification Service** - Push notifications, email/SMS alerts
- **Analytics Service** - Delivery metrics, performance reporting

### Technology Stack
- **Backend**: FastAPI, SQLAlchemy, PostgreSQL, Redis
- **Message Queue**: RabbitMQ/Celery
- **Containerization**: Docker, Docker Compose
- **API Gateway**: Traefik
- **Monitoring**: Prometheus, Grafana
- **Documentation**: OpenAPI/Swagger

## 🚀 Features

### Multi-Tenant Workspace Management
- Workspace-based tenant isolation
- Custom branding (logo, colors)
- Multi-workspace user support
- Role-based access control

### Order Management
- Manual order creation
- RESTful API for partner integrations
- Webhook support
- Real-time status tracking
- Audit logging

### Courier Management
- Mobile app for couriers
- GPS tracking
- Route optimization
- Task assignment (auto/manual)
- Performance analytics

### Notifications
- Push notifications for mobile app
- Email/SMS alerts
- Workspace-specific settings
- Failed delivery notifications

## 🛠️ Development Setup

```bash
# Clone repository
git clone <repository-url>
cd delox

# Start development environment
docker-compose up -d

# Run migrations
docker-compose exec user-service alembic upgrade head
docker-compose exec order-service alembic upgrade head
docker-compose exec courier-service alembic upgrade head

# Access services
# API Gateway: http://localhost:8080
# User Service: http://localhost:8001
# Order Service: http://localhost:8002
# Courier Service: http://localhost:8003
```

## 📁 Project Structure

```
delox/
├── services/
│   ├── api-gateway/          # Traefik configuration
│   ├── auth-service/         # Authentication & authorization
│   ├── user-service/         # User & workspace management
│   ├── order-service/        # Order management
│   ├── courier-service/      # Courier & route management
│   ├── notification-service/ # Notifications
│   └── analytics-service/    # Analytics & reporting
├── shared/
│   ├── models/              # Shared data models
│   ├── utils/               # Common utilities
│   └── middleware/          # Shared middleware
├── docker-compose.yml       # Development environment
├── docker-compose.prod.yml  # Production environment
└── docs/                    # Documentation
```

## 🔐 Security Features

- Multi-tenant data isolation
- JWT-based authentication
- Role-based access control (RBAC)
- API rate limiting
- Audit logging
- Secure API keys per workspace

## 📊 Analytics & Monitoring

- Delivery success rates
- Average delivery times
- Courier performance metrics
- Workspace-wise analytics
- Real-time monitoring dashboards

## 🧪 Testing

```bash
# Run all tests
docker-compose exec user-service pytest
docker-compose exec order-service pytest
docker-compose exec courier-service pytest

# Run with coverage
docker-compose exec user-service pytest --cov=app
```

## 📚 API Documentation

- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc

## 🚀 Deployment

See [deployment guide](docs/deployment.md) for production deployment instructions.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.
