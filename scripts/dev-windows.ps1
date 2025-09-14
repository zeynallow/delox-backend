# Delox Windows Development Script
Write-Host "🔧 Starting Delox in Development Mode..." -ForegroundColor Green

# Check prerequisites
$prerequisites = @("docker", "node", "npm")
foreach ($cmd in $prerequisites) {
    try {
        & $cmd --version | Out-Null
        Write-Host "✅ $cmd is available" -ForegroundColor Green
    } catch {
        Write-Host "❌ $cmd is not available. Please install it first." -ForegroundColor Red
        exit 1
    }
}

# Start backend services only
Write-Host "🐳 Starting backend services..." -ForegroundColor Blue
docker-compose up -d postgres redis rabbitmq auth-service user-service order-service courier-service notification-service analytics-service api-gateway

# Wait for services
Write-Host "⏳ Waiting for backend services..." -ForegroundColor Yellow
Start-Sleep -Seconds 20

# Initialize database
Write-Host "🗄️ Initializing database..." -ForegroundColor Blue
docker-compose exec -T postgres psql -U delox_user -d delox -f /docker-entrypoint-initdb.d/init-db.sql

# Start frontend in development mode
Write-Host "🎨 Starting frontend in development mode..." -ForegroundColor Blue
Set-Location "frontend/admin-dashboard"

Write-Host ""
Write-Host "🎉 Development environment is ready!" -ForegroundColor Green
Write-Host "🔌 Backend API: http://localhost:8080" -ForegroundColor Cyan
Write-Host "📊 Traefik Dashboard: http://localhost:8081" -ForegroundColor Cyan
Write-Host ""
Write-Host "Starting frontend development server..." -ForegroundColor Yellow
Write-Host "Frontend will be available at: http://localhost:3001" -ForegroundColor Cyan

# Start frontend dev server
npm start
