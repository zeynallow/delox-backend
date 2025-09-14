# Delox Windows Startup Script
Write-Host "🚀 Starting Delox Delivery Management System..." -ForegroundColor Green

# Check if Docker is running
try {
    docker version | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Check if .env file exists
if (-not (Test-Path ".env")) {
    Write-Host "📝 Creating .env file from template..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "⚠️  Please edit .env file with your configuration before continuing." -ForegroundColor Yellow
    Write-Host "Press any key to continue after editing .env file..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}

# Install frontend dependencies
Write-Host "📦 Installing frontend dependencies..." -ForegroundColor Blue
Set-Location "frontend/admin-dashboard"
if (Get-Command npm -ErrorAction SilentlyContinue) {
    npm install
    Write-Host "✅ Frontend dependencies installed" -ForegroundColor Green
} else {
    Write-Host "❌ npm not found. Please install Node.js first." -ForegroundColor Red
    Set-Location "../.."
    exit 1
}
Set-Location "../.."

# Start services
Write-Host "🐳 Starting Docker services..." -ForegroundColor Blue
docker-compose up -d

# Wait for services to start
Write-Host "⏳ Waiting for services to start..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Initialize database
Write-Host "🗄️ Initializing database..." -ForegroundColor Blue
docker-compose exec -T postgres psql -U delox_user -d delox -f /docker-entrypoint-initdb.d/init-db.sql

Write-Host ""
Write-Host "🎉 Delox is now running!" -ForegroundColor Green
Write-Host "📱 Admin Dashboard: http://localhost:3000" -ForegroundColor Cyan
Write-Host "🔌 API Gateway: http://localhost:8080" -ForegroundColor Cyan
Write-Host "📊 Traefik Dashboard: http://localhost:8081" -ForegroundColor Cyan
Write-Host ""
Write-Host "To stop the system, run: docker-compose down" -ForegroundColor Yellow
