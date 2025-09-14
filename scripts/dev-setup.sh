#!/bin/bash

# Delox Development Setup Script

set -e

echo "🚀 Setting up Delox development environment..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please update the .env file with your configuration before continuing."
    echo "   Especially update the JWT_SECRET_KEY and API keys."
fi

# Build Docker images
echo "🔨 Building Docker images..."
docker-compose build

# Start services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 15

# Check service health
echo "🔍 Checking service health..."

services=("auth-service" "user-service" "order-service")
for service in "${services[@]}"; do
    echo "Checking $service..."
    if curl -f http://localhost:8080/api/v1/${service}/health > /dev/null 2>&1; then
        echo "✅ $service is healthy"
    else
        echo "❌ $service is not responding"
    fi
done

# Run database migrations
echo "🗄️  Running database migrations..."
docker-compose exec -T auth-service alembic upgrade head || echo "⚠️  Auth service migrations failed"
docker-compose exec -T user-service alembic upgrade head || echo "⚠️  User service migrations failed"
docker-compose exec -T order-service alembic upgrade head || echo "⚠️  Order service migrations failed"

echo ""
echo "🎉 Development environment setup complete!"
echo ""
echo "📋 Available services:"
echo "   • API Gateway: http://localhost:8080"
echo "   • Auth Service: http://localhost:8080/api/v1/auth/docs"
echo "   • User Service: http://localhost:8080/api/v1/users/docs"
echo "   • Order Service: http://localhost:8080/api/v1/orders/docs"
echo "   • Traefik Dashboard: http://localhost:8081"
echo "   • RabbitMQ Management: http://localhost:15672 (delox/delox_password)"
echo ""
echo "🔧 Useful commands:"
echo "   • View logs: docker-compose logs -f"
echo "   • Stop services: docker-compose down"
echo "   • Restart services: docker-compose restart"
echo "   • Run tests: make test"
echo ""
echo "📖 Next steps:"
echo "   1. Update .env file with your API keys"
echo "   2. Test the API endpoints using the Swagger docs"
echo "   3. Create your first workspace and user"
echo ""
