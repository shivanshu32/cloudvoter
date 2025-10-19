@echo off
echo ========================================
echo CloudVoter Local Development Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.11 or higher from python.org
    pause
    exit /b 1
)

echo [OK] Python is installed
echo.

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed or not in PATH
    echo Please install Node.js from nodejs.org
    pause
    exit /b 1
)

echo [OK] Node.js is installed
echo.

REM Setup Backend
echo ========================================
echo Setting up Backend...
echo ========================================
cd backend

echo Creating virtual environment...
python -m venv venv

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing Python dependencies...
pip install -r requirements.txt

echo Installing Playwright browsers...
playwright install chromium

echo.
echo [OK] Backend setup complete!
echo.

cd ..

REM Setup Frontend
echo ========================================
echo Setting up Frontend...
echo ========================================
cd frontend

echo Installing Node.js dependencies...
call npm install

echo.
echo [OK] Frontend setup complete!
echo.

cd ..

REM Create directories
echo ========================================
echo Creating directories...
echo ========================================
if not exist "brightdata_session_data" mkdir brightdata_session_data
if not exist "failure_screenshots" mkdir failure_screenshots

echo.
echo [OK] Directories created!
echo.

REM Create .env file if it doesn't exist
if not exist ".env" (
    echo Creating .env file...
    copy .env.example .env
    echo [OK] .env file created - please edit with your credentials
) else (
    echo [OK] .env file already exists
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To start the application:
echo.
echo 1. Start Backend (in one terminal):
echo    cd backend
echo    venv\Scripts\activate
echo    python app.py
echo.
echo 2. Start Frontend (in another terminal):
echo    cd frontend
echo    npm start
echo.
echo 3. Open browser:
echo    http://localhost:3000
echo.
echo ========================================
pause
