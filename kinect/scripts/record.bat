@echo off
:: Records until you press Ctrl-C.  Settings come from config.bat.
setlocal
call "%~dp0config.bat"

if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

set /p FILENAME="Enter output filename (without extension, e.g. take-01): "
if "%FILENAME%"=="" (
    echo No filename entered. Exiting.
    pause
    exit /b 1
)

set OUTPUT=%OUTPUT_DIR%\%FILENAME%.mkv

echo.
echo Color   : %COLOR_MODE%
echo Depth   : %DEPTH_MODE%
echo Rate    : %FRAME_RATE% fps
echo IMU     : %IMU%
echo Saving to: %OUTPUT%
echo.
echo Press Ctrl-C to stop recording.
echo.

"%K4A_RECORDER%" -c %COLOR_MODE% -d %DEPTH_MODE% -r %FRAME_RATE% --imu %IMU% "%OUTPUT%"

echo.
echo Recording saved to %OUTPUT%
pause
