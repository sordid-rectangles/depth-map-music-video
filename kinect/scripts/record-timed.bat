@echo off
:: Records for a fixed number of seconds.  Settings come from config.bat.
setlocal
call "%~dp0config.bat"

set OUTPUT_DIR=%~dp0..\output
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

set /p FILENAME="Enter output filename (without extension, e.g. take-01): "
if "%FILENAME%"=="" (
    echo No filename entered. Exiting.
    pause
    exit /b 1
)

set /p SECONDS="Enter recording duration in seconds: "
if "%SECONDS%"=="" (
    echo No duration entered. Exiting.
    pause
    exit /b 1
)

set OUTPUT=%OUTPUT_DIR%\%FILENAME%.mkv

echo.
echo Color   : %COLOR_MODE%
echo Depth   : %DEPTH_MODE%
echo Rate    : %FRAME_RATE% fps
echo IMU     : %IMU%
echo Duration: %SECONDS% seconds
echo Saving to: %OUTPUT%
echo.

"%K4A_RECORDER%" -c %COLOR_MODE% -d %DEPTH_MODE% -r %FRAME_RATE% --imu %IMU% -l %SECONDS% "%OUTPUT%"

echo.
echo Done. Recording saved to %OUTPUT%
pause
