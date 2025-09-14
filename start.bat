@echo off
echo 🚀 Starting Delox Delivery Management System...

REM Check if Docker is running
docker version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)
echo ✅ Docker is running

REM Check if .env file exists
if not exist ".env" (
    echo 📝 Creating .env file from template...
    copy ".env.example" ".env"
    echo ⚠️  Please edit .env file with your configuration before continuing.
    pause
)

REM Install frontend dependencies
echo 📦 Installing frontend dependencies...
cd frontend\admin-dashboard
npm install

if %errorlevel% neq 0 (
    echo ❌ Failed to install frontend dependencies. Please install Node.js first.
    pause
    exit /b 1
)
cd ..\..
echo ✅ Frontend dependencies installed

REM Start services
echo 🐳 Starting Docker services...
docker-compose up -d

REM Wait for services to start
echo ⏳ Waiting for services to start...
timeout /t 30 /nobreak >nul

REM Initialize database
echo 🗄️ Initializing database...
docker-compose exec -T postgres psql -U delox_user -d delox -f /docker-entrypoint-initdb.d/init-db.sql

echo.
echo 🎉 Delox is now running!
echo 📱 Admin Dashboard: http://localhost:3000
echo 🔌 API Gateway: http://localhost:8080
echo 📊 Traefik Dashboard: http://localhost:8081
echo.
echo To stop the system, run: stop.bat
pause
