@echo off
:: Records until you press Ctrl-C.  Settings come from config.bat.
setlocal
call "%~dp0config.bat"

:: Resolve output location
set DEFAULT_OUTPUT_DIR=%~dp0..\output
set EXTERNAL_OUTPUT_DIR=
if exist "%~dp0external-output.bat" call "%~dp0external-output.bat"

if "%EXTERNAL_OUTPUT_DIR%"=="" (
    set OUTPUT_DIR=%DEFAULT_OUTPUT_DIR%
) else (
    echo Where should the recording be saved?
    echo   [1] Default   %DEFAULT_OUTPUT_DIR%
    echo   [2] External  %EXTERNAL_OUTPUT_DIR%
    echo.
    choice /c 12 /n /m "Choose: "
    if errorlevel 2 (set OUTPUT_DIR=%EXTERNAL_OUTPUT_DIR%) else (set OUTPUT_DIR=%DEFAULT_OUTPUT_DIR%)
)

if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

echo.
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
