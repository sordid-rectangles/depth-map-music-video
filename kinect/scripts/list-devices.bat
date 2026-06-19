@echo off
call "%~dp0config.bat"
echo Listing connected Azure Kinect devices...
echo.
"%K4A_RECORDER%" --list
echo.
pause
