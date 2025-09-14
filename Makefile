# Delox Development Makefile

.PHONY: help build up down logs clean test lint format install-dev

# Default target
help:
	@echo "Available commands:"
	@echo "  build       - Build all Docker images"
	@echo "  up          - Start all services"
	@echo "  down        - Stop all services"
	@echo "  logs        - Show logs from all services"
	@echo "  clean       - Clean up Docker resources"
	@echo "  test        - Run tests for all services"
	@echo "  lint        - Run linting for all services"
	@echo "  format      - Format code for all services"
	@echo "  install-dev - Install development dependencies"

# Docker commands
build:
	docker-compose build

up:
	docker-compose up -d

down:
	docker-compose down

logs:
	docker-compose logs -f

clean:
	docker-compose down -v --remove-orphans
	docker system prune -f

# Development commands
install-dev:
	@echo "Installing development dependencies..."
	cd services/auth-service && pip install -r requirements.txt
	cd services/user-service && pip install -r requirements.txt
	cd services/order-service && pip install -r requirements.txt

test:
	@echo "Running tests for all services..."
	docker-compose exec auth-service pytest
	docker-compose exec user-service pytest
	docker-compose exec order-service pytest

lint:
	@echo "Running linting for all services..."
	docker-compose exec auth-service flake8 app/
	docker-compose exec user-service flake8 app/
	docker-compose exec order-service flake8 app/

format:
	@echo "Formatting code for all services..."
	docker-compose exec auth-service black app/
	docker-compose exec user-service black app/
	docker-compose exec order-service black app/

# Database commands
migrate:
	@echo "Running database migrations..."
	docker-compose exec auth-service alembic upgrade head
	docker-compose exec user-service alembic upgrade head
	docker-compose exec order-service alembic upgrade head

migrate-create:
	@echo "Creating new migration..."
	@read -p "Enter service name (auth/user/order): " service; \
	read -p "Enter migration message: " message; \
	docker-compose exec $$service-service alembic revision --autogenerate -m "$$message"

# Service-specific commands
auth-logs:
	docker-compose logs -f auth-service

user-logs:
	docker-compose logs -f user-service

order-logs:
	docker-compose logs -f order-service

courier-logs:
	docker-compose logs -f courier-service

notification-logs:
	docker-compose logs -f notification-service

analytics-logs:
	docker-compose logs -f analytics-service

# Quick development setup
dev-setup: build up
	@echo "Waiting for services to start..."
	sleep 10
	make migrate
	@echo "Development environment ready!"

# Production deployment
prod-build:
	docker-compose -f docker-compose.prod.yml build

prod-up:
	docker-compose -f docker-compose.prod.yml up -d

prod-down:
	docker-compose -f docker-compose.prod.yml down
