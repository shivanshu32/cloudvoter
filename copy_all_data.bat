@echo off
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║                                                               ║
echo ║   Copy All Data from GoogleLoginAutomate to CloudVoter       ║
echo ║                                                               ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

set SOURCE_DIR=c:\Users\shubh\OneDrive\Desktop\googleloginautomate
set DEST_DIR=c:\Users\shubh\OneDrive\Desktop\cloudvoter

echo Source: %SOURCE_DIR%
echo Destination: %DEST_DIR%
echo.

REM ========================================
REM Copy Session Data
REM ========================================
echo ========================================
echo Step 1: Copying Session Data
echo ========================================
echo.

set SESSION_SOURCE=%SOURCE_DIR%\brightdata_session_data
set SESSION_DEST=%DEST_DIR%\brightdata_session_data

if not exist "%SESSION_SOURCE%" (
    echo [WARNING] Session data folder not found
    echo Location: %SESSION_SOURCE%
    echo.
    echo This is OK if you haven't saved any sessions yet.
    echo.
) else (
    echo Creating destination folder...
    if not exist "%SESSION_DEST%" mkdir "%SESSION_DEST%"
    
    echo Copying session data...
    xcopy "%SESSION_SOURCE%" "%SESSION_DEST%" /E /I /H /Y
    
    if errorlevel 1 (
        echo [ERROR] Session data copy failed
        pause
        exit /b 1
    )
    
    echo.
    echo [SUCCESS] Session data copied!
    echo.
    echo Sessions found:
    dir "%SESSION_DEST%" /B | find /c "instance_"
    echo.
)

REM ========================================
REM Copy Voting Logs
REM ========================================
echo ========================================
echo Step 2: Copying Voting Logs
echo ========================================
echo.

set LOGS_SOURCE=%SOURCE_DIR%\voting_logs.csv
set LOGS_DEST=%DEST_DIR%\voting_logs.csv

if not exist "%LOGS_SOURCE%" (
    echo [WARNING] voting_logs.csv not found
    echo Location: %LOGS_SOURCE%
    echo.
    echo This is OK if you haven't run the system yet.
    echo A new voting_logs.csv will be created automatically.
    echo.
) else (
    echo Copying voting_logs.csv...
    copy "%LOGS_SOURCE%" "%LOGS_DEST%" /Y
    
    if errorlevel 1 (
        echo [ERROR] Voting logs copy failed
        pause
        exit /b 1
    )
    
    echo.
    echo [SUCCESS] Voting logs copied!
    echo.
    echo File size:
    dir "%LOGS_DEST%" | find "voting_logs.csv"
    echo.
)

REM ========================================
REM Create failure_screenshots folder
REM ========================================
echo ========================================
echo Step 3: Creating Directories
echo ========================================
echo.

if not exist "%DEST_DIR%\failure_screenshots" (
    mkdir "%DEST_DIR%\failure_screenshots"
    echo [SUCCESS] Created failure_screenshots folder
) else (
    echo [OK] failure_screenshots folder already exists
)

echo.

REM ========================================
REM Summary
REM ========================================
echo ╔═══════════════════════════════════════════════════════════════╗
echo ║                                                               ║
echo ║   ✅ DATA COPY COMPLETE!                                     ║
echo ║                                                               ║
echo ╚═══════════════════════════════════════════════════════════════╝
echo.

echo What was copied:
echo.
echo ✓ Session Data (brightdata_session_data/)
if exist "%SESSION_DEST%" (
    echo   - Contains saved Google logins
    echo   - Contains voting history per instance
    echo   - Contains browser state
) else (
    echo   - Not found (will be created on first run)
)
echo.

echo ✓ Voting Logs (voting_logs.csv)
if exist "%LOGS_DEST%" (
    echo   - Contains complete voting history
    echo   - Used for cooldown detection
    echo   - Used for statistics
) else (
    echo   - Not found (will be created on first run)
)
echo.

echo ✓ Directories
echo   - failure_screenshots/ (for error screenshots)
echo.

echo ========================================
echo Next Steps:
echo ========================================
echo.
echo 1. Review copied data in cloudvoter folder
echo 2. Follow QUICKSTART.md to deploy
echo 3. Click "Start Ultra Monitoring"
echo 4. System will use existing sessions and logs!
echo.

pause
