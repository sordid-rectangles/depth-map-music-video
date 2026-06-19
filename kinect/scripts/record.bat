@echo off
:: Prompts for an output filename then records until Ctrl-C.
:: Settings: RGB 1440p, depth WFOV_2X2BINNED, 30fps, IMU off. No audio (k4arecorder never records audio).

setlocal

set /p FILENAME="Enter output filename (without extension, e.g. take-01): "
if "%FILENAME%"=="" (
    echo No filename entered. Exiting.
    pause
    exit /b 1
)

set OUTPUT=%FILENAME%.mkv

echo.
echo Recording to %OUTPUT%
echo Press Ctrl-C to stop recording.
echo.

k4arecorder.exe -c 1440p -d WFOV_2X2BINNED -r 30 --imu OFF "%OUTPUT%"

echo.
echo Recording saved to %OUTPUT%
pause
