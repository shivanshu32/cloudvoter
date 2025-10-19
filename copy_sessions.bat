@echo off
echo ========================================
echo Copying Session Data from GoogleLoginAutomate
echo ========================================
echo.

set SOURCE=c:\Users\shubh\OneDrive\Desktop\googleloginautomate\brightdata_session_data
set DEST=c:\Users\shubh\OneDrive\Desktop\cloudvoter\brightdata_session_data

echo Source: %SOURCE%
echo Destination: %DEST%
echo.

if not exist "%SOURCE%" (
    echo [ERROR] Source folder not found: %SOURCE%
    pause
    exit /b 1
)

echo Creating destination folder...
if not exist "%DEST%" mkdir "%DEST%"

echo.
echo Copying session data...
xcopy "%SOURCE%" "%DEST%" /E /I /H /Y

if errorlevel 1 (
    echo [ERROR] Copy failed
    pause
    exit /b 1
)

echo.
echo ========================================
echo [SUCCESS] Session data copied!
echo ========================================
echo.

echo Checking copied sessions...
dir "%DEST%" /B

echo.
echo Session data is now available in cloudvoter project.
echo You can now deploy CloudVoter with existing sessions.
echo.
pause
