@echo off
setlocal

set EXT_CONFIG=%~dp0external-output.bat

set EXTERNAL_OUTPUT_DIR=
if exist "%EXT_CONFIG%" call "%EXT_CONFIG%"

cls
echo ============================================================
echo   EXTERNAL DRIVE OUTPUT FOLDER
echo ============================================================
echo.
if "%EXTERNAL_OUTPUT_DIR%"=="" (
    echo   No external drive configured.
    echo   Recordings currently save to the default kinect\output folder.
) else (
    echo   Current external drive path:
    echo   %EXTERNAL_OUTPUT_DIR%
)
echo.
echo   Paste the path to the folder on the external drive and press Enter.
echo   Example: E:\kinect-recordings
echo.
echo   Leave blank and press Enter to clear the external drive setting.
echo.
set /p NEW_PATH="  Path: "

if "%NEW_PATH%"=="" (
    if exist "%EXT_CONFIG%" del "%EXT_CONFIG%"
    echo.
    echo External drive cleared.
    echo Recordings will use the default kinect\output folder.
) else (
    echo set EXTERNAL_OUTPUT_DIR=%NEW_PATH%> "%EXT_CONFIG%"
    echo.
    echo External drive set to: %NEW_PATH%
    echo This will be offered as an option when you start recording.
)
echo.
pause
