@echo off
echo ========================================
echo CloudVoter Backend Deployment Package
echo ========================================
echo.

REM Clean up old package
if exist backend_deploy (
    echo Removing old deployment package...
    rmdir /s /q backend_deploy
)

echo Creating deployment package...
mkdir backend_deploy

echo.
echo [1/5] Copying backend files...
xcopy backend\*.py backend_deploy\ /Y >nul
xcopy backend\requirements*.txt backend_deploy\ /Y >nul
if errorlevel 1 (
    echo ERROR: Failed to copy backend files
    pause
    exit /b 1
)
echo ✅ Backend files copied

echo.
echo [2/5] Copying session data...
if exist brightdata_session_data (
    xcopy brightdata_session_data backend_deploy\brightdata_session_data\ /E /I /Y >nul
    echo ✅ Session data copied
) else (
    echo ⚠️  WARNING: brightdata_session_data folder not found!
    echo    Make sure session data exists before deploying
)

echo.
echo [3/5] Copying voting logs...
if exist voting_logs.csv (
    copy voting_logs.csv backend_deploy\ /Y >nul
    echo ✅ Voting logs copied
) else (
    echo Creating empty voting logs file...
    echo timestamp,instance_id,vote_status,ip_address,session_status > backend_deploy\voting_logs.csv
    echo ✅ Empty voting logs created
)

echo.
echo [4/5] Creating deployment files...

REM Create Dockerfile
(
echo FROM python:3.11-slim
echo.
echo WORKDIR /app
echo.
echo # Install system dependencies for Playwright
echo RUN apt-get update ^&^& apt-get install -y \
echo     wget \
echo     gnupg \
echo     ca-certificates \
echo     fonts-liberation \
echo     libasound2 \
echo     libatk-bridge2.0-0 \
echo     libatk1.0-0 \
echo     libatspi2.0-0 \
echo     libcups2 \
echo     libdbus-1-3 \
echo     libdrm2 \
echo     libgbm1 \
echo     libgtk-3-0 \
echo     libnspr4 \
echo     libnss3 \
echo     libwayland-client0 \
echo     libxcomposite1 \
echo     libxdamage1 \
echo     libxfixes3 \
echo     libxkbcommon0 \
echo     libxrandr2 \
echo     xdg-utils \
echo     ^&^& rm -rf /var/lib/apt/lists/*
echo.
echo # Copy requirements
echo COPY requirements.txt .
echo RUN pip install --no-cache-dir -r requirements.txt
echo.
echo # Install Playwright browsers
echo RUN playwright install chromium
echo RUN playwright install-deps chromium
echo.
echo # Copy application files
echo COPY *.py ./
echo COPY brightdata_session_data/ ./brightdata_session_data/
echo COPY voting_logs.csv ./
echo.
echo # Create necessary directories
echo RUN mkdir -p templates
echo.
echo # Expose port
echo EXPOSE 5000
echo.
echo # Run application
echo CMD ["python", "app.py"]
) > backend_deploy\Dockerfile
echo ✅ Dockerfile created

REM Create docker-compose.yml
(
echo version: '3.8'
echo.
echo services:
echo   cloudvoter-backend:
echo     build: .
echo     container_name: cloudvoter-backend
echo     ports:
echo       - "5000:5000"
echo     volumes:
echo       - ./brightdata_session_data:/app/brightdata_session_data
echo       - ./voting_logs.csv:/app/voting_logs.csv
echo       - ./cloudvoter.log:/app/cloudvoter.log
echo     environment:
echo       - PYTHONUNBUFFERED=1
echo     restart: unless-stopped
echo     deploy:
echo       resources:
echo         limits:
echo           cpus: '2'
echo           memory: 3G
) > backend_deploy\docker-compose.yml
echo ✅ docker-compose.yml created

REM Create deploy.sh
(
echo #!/bin/bash
echo set -e
echo.
echo echo "=========================================="
echo echo "CloudVoter Backend Deployment"
echo echo "=========================================="
echo echo ""
echo.
echo echo "Updating system packages..."
echo apt-get update
echo apt-get upgrade -y
echo.
echo echo "Installing Docker..."
echo if ! command -v docker ^&^>/dev/null; then
echo     curl -fsSL https://get.docker.com -o get-docker.sh
echo     sh get-docker.sh
echo     rm get-docker.sh
echo     echo "✅ Docker installed"
echo else
echo     echo "✅ Docker already installed"
echo fi
echo.
echo echo "Installing Docker Compose..."
echo if ! command -v docker-compose ^&^>/dev/null; then
echo     curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$^(uname -s^)-$^(uname -m^)" -o /usr/local/bin/docker-compose
echo     chmod +x /usr/local/bin/docker-compose
echo     echo "✅ Docker Compose installed"
echo else
echo     echo "✅ Docker Compose already installed"
echo fi
echo.
echo echo "Building Docker image..."
echo docker-compose build
echo.
echo echo "Starting CloudVoter backend..."
echo docker-compose up -d
echo.
echo echo "=========================================="
echo echo "✅ CloudVoter Backend is running!"
echo echo "=========================================="
echo echo ""
echo echo "Backend API: http://$^(curl -s ifconfig.me^):5000"
echo echo "Health check: http://$^(curl -s ifconfig.me^):5000/api/health"
echo echo ""
echo echo "View logs: docker-compose logs -f"
echo echo "Stop: docker-compose down"
echo echo "Restart: docker-compose restart"
echo echo ""
) > backend_deploy\deploy.sh
echo ✅ deploy.sh created

REM Create .env template
(
echo # Bright Data Credentials
echo BRIGHT_DATA_USERNAME=hl_47ba96ab
echo BRIGHT_DATA_PASSWORD=your-password-here
echo.
echo # Flask Configuration
echo SECRET_KEY=change-this-to-secure-random-key
echo.
echo # Voting Configuration
echo TARGET_URL=https://www.cutebabyvote.com/vote/...
) > backend_deploy\.env
echo ✅ .env template created

REM Create README
(
echo # CloudVoter Backend Deployment Package
echo.
echo ## Quick Start
echo.
echo 1. Edit .env file with your credentials
echo 2. Upload to DigitalOcean: scp cloudvoter-backend.tar.gz root@YOUR_IP:/root/
echo 3. SSH to droplet: ssh root@YOUR_IP
echo 4. Extract: mkdir cloudvoter-backend ^&^& cd cloudvoter-backend ^&^& tar -xzf ../cloudvoter-backend.tar.gz
echo 5. Deploy: chmod +x deploy.sh ^&^& ./deploy.sh
echo.
echo ## Files Included
echo.
echo - app.py - Main Flask application
echo - voter_engine.py - Voting automation engine
echo - config.py - Configuration
echo - vote_logger.py - Logging utility
echo - brightdata_session_data/ - Saved sessions
echo - voting_logs.csv - Voting history
echo - Dockerfile - Docker image definition
echo - docker-compose.yml - Docker Compose configuration
echo - deploy.sh - Automated deployment script
echo - .env - Environment variables ^(EDIT THIS!^)
echo.
echo ## Documentation
echo.
echo See BACKEND_ONLY_DEPLOYMENT.md for complete instructions.
) > backend_deploy\README.txt
echo ✅ README.txt created

echo.
echo [5/5] Creating archive...
cd backend_deploy
where tar >nul 2>&1
if %errorlevel% equ 0 (
    tar -czf ..\cloudvoter-backend.tar.gz *
    cd ..
    echo ✅ Archive created: cloudvoter-backend.tar.gz
) else (
    cd ..
    echo ⚠️  tar command not found
    echo.
    echo Please create archive manually:
    echo 1. Install 7-Zip or WinRAR
    echo 2. Right-click backend_deploy folder
    echo 3. Create tar.gz archive named: cloudvoter-backend.tar.gz
)

echo.
echo ========================================
echo ✅ Backend Package Ready!
echo ========================================
echo.
echo Package location: backend_deploy\
echo Archive: cloudvoter-backend.tar.gz
echo.
echo 📋 IMPORTANT NEXT STEPS:
echo.
echo 1. Edit backend_deploy\.env file:
echo    - Set BRIGHT_DATA_PASSWORD to your actual password
echo    - Generate SECRET_KEY: python -c "import secrets; print(secrets.token_hex(32))"
echo    - Verify TARGET_URL
echo.
echo 2. Upload to DigitalOcean:
echo    scp cloudvoter-backend.tar.gz root@YOUR_DROPLET_IP:/root/
echo.
echo 3. Follow BACKEND_ONLY_DEPLOYMENT.md for deployment steps
echo.
echo ========================================

REM Show package statistics
echo.
echo 📦 Package Contents:
dir backend_deploy /b
echo.

REM Count session instances
if exist backend_deploy\brightdata_session_data (
    echo 📊 Session Data Statistics:
    for /f %%i in ('dir backend_deploy\brightdata_session_data /b /ad ^| find /c /v ""') do echo    %%i session instances found
)

REM Show voting logs size
if exist backend_deploy\voting_logs.csv (
    for %%A in (backend_deploy\voting_logs.csv) do (
        set size=%%~zA
        if %%~zA GTR 1048576 (
            set /a mb=%%~zA/1048576
            echo    Voting logs: !mb! MB
        ) else if %%~zA GTR 1024 (
            set /a kb=%%~zA/1024
            echo    Voting logs: !kb! KB
        ) else (
            echo    Voting logs: %%~zA bytes
        )
    )
)

echo.
echo 🚀 Ready to deploy!
echo.
pause
