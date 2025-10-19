@echo off
echo ========================================
echo Copying Voting Logs from GoogleLoginAutomate
echo ========================================
echo.

set SOURCE=c:\Users\shubh\OneDrive\Desktop\googleloginautomate\voting_logs.csv
set DEST=c:\Users\shubh\OneDrive\Desktop\cloudvoter\voting_logs.csv

echo Source: %SOURCE%
echo Destination: %DEST%
echo.

if not exist "%SOURCE%" (
    echo [WARNING] voting_logs.csv not found in googleloginautomate
    echo This is OK if you haven't run the system yet.
    echo A new voting_logs.csv will be created automatically.
    echo.
    pause
    exit /b 0
)

echo Copying voting_logs.csv...
copy "%SOURCE%" "%DEST%" /Y

if errorlevel 1 (
    echo [ERROR] Copy failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo [SUCCESS] Voting logs copied!
echo ========================================
echo.

echo Checking file size...
dir "%DEST%"

echo.
echo Voting logs are now available in cloudvoter project.
echo This file contains voting history and helps with:
echo - Cooldown detection
echo - Instance launch decisions
echo - Statistics and tracking
echo.
pause
