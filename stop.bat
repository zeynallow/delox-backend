@echo off
echo 🛑 Stopping Delox Delivery Management System...

echo 🐳 Stopping Docker services...
docker-compose down

echo ✅ All services stopped successfully!
echo.
echo To start again, run: start.bat
pause
