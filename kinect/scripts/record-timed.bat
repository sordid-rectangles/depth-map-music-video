@echo off
:: Prompts for a filename and duration, then records for exactly N seconds.
:: Settings: RGB 1440p, depth WFOV_2X2BINNED, 30fps, IMU off. No audio (k4arecorder never records audio).

setlocal

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

set OUTPUT=%FILENAME%.mkv

echo.
echo Recording %SECONDS% seconds to %OUTPUT% ...
echo.

k4arecorder.exe -c 1440p -d WFOV_2X2BINNED -r 30 --imu OFF -l %SECONDS% "%OUTPUT%"

echo.
echo Done. Recording saved to %OUTPUT%
pause
