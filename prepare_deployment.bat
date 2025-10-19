@echo off
echo ========================================
echo CloudVoter Deployment Package Creator
echo ========================================
echo.

REM Clean up old deployment package
if exist deploy_package (
    echo Removing old deployment package...
    rmdir /s /q deploy_package
)

echo Creating deployment package structure...
mkdir deploy_package
mkdir deploy_package\backend
mkdir deploy_package\frontend

echo.
echo [1/8] Copying backend Python files...
xcopy backend\*.py deploy_package\backend\ /Y >nul
if errorlevel 1 (
    echo ERROR: Failed to copy backend files
    pause
    exit /b 1
)
echo ✅ Backend files copied

echo.
echo [2/8] Copying requirements files...
xcopy backend\requirements*.txt deploy_package\backend\ /Y >nul
echo ✅ Requirements files copied

echo.
echo [3/8] Copying session data...
if exist brightdata_session_data (
    xcopy brightdata_session_data deploy_package\backend\brightdata_session_data\ /E /I /Y >nul
    echo ✅ Session data copied
) else (
    echo ⚠️  WARNING: brightdata_session_data folder not found!
    echo    Run copy_all_data.bat first to copy session data
)

echo.
echo [4/8] Copying voting logs...
if exist voting_logs.csv (
    copy voting_logs.csv deploy_package\backend\ /Y >nul
    echo ✅ Voting logs copied
) else (
    echo ⚠️  WARNING: voting_logs.csv not found!
    echo    Creating empty voting logs file...
    echo timestamp,instance_id,vote_status,ip_address,session_status > deploy_package\backend\voting_logs.csv
)

echo.
echo [5/8] Copying Docker files...
copy Dockerfile deploy_package\ /Y >nul
copy docker-compose.yml deploy_package\ /Y >nul
copy nginx.conf deploy_package\ /Y >nul
copy deploy.sh deploy_package\ /Y >nul
echo ✅ Docker files copied

echo.
echo [6/8] Creating .env file from template...
if exist .env.example (
    copy .env.example deploy_package\.env /Y >nul
    echo ✅ .env file created
) else (
    echo Creating default .env file...
    (
        echo # Flask Configuration
        echo SECRET_KEY=change-this-to-a-secure-random-key
        echo.
        echo # Bright Data Credentials
        echo BRIGHT_DATA_USERNAME=hl_47ba96ab
        echo BRIGHT_DATA_PASSWORD=your-password-here
        echo.
        echo # Voting Configuration
        echo TARGET_URL=https://www.cutebabyvote.com/vote/...
    ) > deploy_package\.env
    echo ✅ Default .env file created
)

echo.
echo [7/8] Checking for frontend build...
if exist frontend\build (
    echo Copying frontend build...
    xcopy frontend\build deploy_package\frontend\build\ /E /I /Y >nul
    echo ✅ Frontend build copied
) else (
    echo ⚠️  WARNING: Frontend build not found!
    echo.
    echo To build frontend, run:
    echo   cd frontend
    echo   npm run build
    echo   cd ..
    echo.
    echo Then run this script again.
)

echo.
echo [8/8] Creating archive...
cd deploy_package
if exist ..\cloudvoter-deploy.tar.gz (
    del ..\cloudvoter-deploy.tar.gz
)

REM Try to create tar.gz archive
where tar >nul 2>&1
if %errorlevel% equ 0 (
    tar -czf ..\cloudvoter-deploy.tar.gz *
    echo ✅ Archive created: cloudvoter-deploy.tar.gz
) else (
    echo ⚠️  tar command not found
    echo.
    echo Please manually create archive:
    echo 1. Install 7-Zip or WinRAR
    echo 2. Right-click deploy_package folder
    echo 3. Create tar.gz archive named: cloudvoter-deploy.tar.gz
)
cd ..

echo.
echo ========================================
echo ✅ Deployment Package Ready!
echo ========================================
echo.
echo Package location: deploy_package\
echo Archive: cloudvoter-deploy.tar.gz
echo.
echo 📋 IMPORTANT NEXT STEPS:
echo.
echo 1. Edit deploy_package\.env file:
echo    - Set SECRET_KEY to a secure random string
echo    - Verify BRIGHT_DATA_USERNAME
echo    - Set BRIGHT_DATA_PASSWORD
echo    - Update TARGET_URL if needed
echo.
echo 2. Generate secure SECRET_KEY:
echo    python -c "import secrets; print(secrets.token_hex(32))"
echo.
echo 3. Upload to DigitalOcean:
echo    scp cloudvoter-deploy.tar.gz root@YOUR_DROPLET_IP:/root/
echo.
echo 4. Follow DIGITALOCEAN_DEPLOYMENT_COMPLETE.md for full instructions
echo.
echo ========================================

REM Show package contents
echo.
echo 📦 Package Contents:
dir deploy_package /b
echo.

REM Show session data count
if exist deploy_package\backend\brightdata_session_data (
    echo 📊 Session Data:
    dir deploy_package\backend\brightdata_session_data /b | find /c /v ""
    echo    instances found
)

echo.
pause
