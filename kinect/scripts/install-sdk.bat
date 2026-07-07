@echo off
:: Azure Kinect SDK v1.4.2 — must run as Administrator.
:: Right-click this file > Run as administrator

net session >nul 2>&1
if errorlevel 1 (
    echo.
    echo ERROR: This installer needs Administrator rights.
    echo Right-click install-sdk.bat and choose "Run as administrator".
    echo.
    pause
    exit /b 1
)

set SDK_VERSION=1.4.2
set INSTALLER=%TEMP%\Azure-Kinect-SDK-%SDK_VERSION%.exe
set SDK_URL=https://download.microsoft.com/download/d/c/1/dc1f8a76-1ef2-4a1a-ac89-a7e22b3da491/Azure%%20Kinect%%20SDK%%201.4.2.exe
set RECORDER=C:\Program Files\Azure Kinect SDK v%SDK_VERSION%\tools\k4arecorder.exe

if exist "%RECORDER%" (
    echo Azure Kinect SDK %SDK_VERSION% is already installed.
    goto VERIFY
)

if not exist "%INSTALLER%" (
    echo Downloading Azure Kinect SDK %SDK_VERSION%...
    powershell -NoProfile -Command "Invoke-WebRequest -Uri '%SDK_URL%' -OutFile '%INSTALLER%' -UseBasicParsing"
    if errorlevel 1 (
        echo Download failed.
        pause
        exit /b 1
    )
)

echo.
echo Starting SDK installer — use the default install location.
echo.
start /wait "" "%INSTALLER%"

:VERIFY
if not exist "%RECORDER%" (
    echo.
    echo ERROR: Install finished but k4arecorder was not found at:
    echo   %RECORDER%
    echo If you chose a custom path, update recorder_path in operator-config.json.
    echo.
    pause
    exit /b 1
)

echo.
echo SDK installed successfully.
echo   %RECORDER%
echo.
"%RECORDER%" --list
echo.
pause
