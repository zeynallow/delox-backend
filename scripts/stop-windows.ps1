# Delox Windows Stop Script
Write-Host "🛑 Stopping Delox Delivery Management System..." -ForegroundColor Red

# Stop all services
Write-Host "🐳 Stopping Docker services..." -ForegroundColor Blue
docker-compose down

Write-Host "✅ All services stopped successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "To start again, run: .\scripts\start-windows.ps1" -ForegroundColor Yellow
