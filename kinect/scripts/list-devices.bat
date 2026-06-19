@echo off
call "%~dp0config.bat"

echo Checking for connected Azure Kinect devices...
echo (Waiting a moment for USB to settle...)
timeout /t 3 /nobreak > nul

echo.
"%K4A_RECORDER%" --list
if errorlevel 1 (
    echo.
    echo ERROR: Could not reach k4arecorder.
    echo Check that the path in config.bat is correct:
    echo   %K4A_RECORDER%
)
echo.
pause
