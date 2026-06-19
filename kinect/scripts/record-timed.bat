@echo off
:: Records for a fixed number of seconds.  Settings come from config.bat.
setlocal
call "%~dp0config.bat"

:: Resolve output location
set DEFAULT_OUTPUT_DIR=%~dp0..\output
set EXTERNAL_OUTPUT_DIR=
if exist "%~dp0external-output.bat" call "%~dp0external-output.bat"

if "%EXTERNAL_OUTPUT_DIR%"=="" (
    set OUTPUT_DIR=%DEFAULT_OUTPUT_DIR%
) else (
    for %%P in ("%EXTERNAL_OUTPUT_DIR%") do set EXT_DRIVE=%%~dP
    if not exist "%EXT_DRIVE%\" (
        echo.
        echo WARNING: External drive not found at %EXT_DRIVE%
        echo The drive letter may have changed since set-output.bat was last run.
        echo Run set-output.bat to update the path, then try again.
        echo Falling back to default output folder.
        echo.
        set OUTPUT_DIR=%DEFAULT_OUTPUT_DIR%
    ) else (
        echo Where should the recording be saved?
        echo   [1] Default   %DEFAULT_OUTPUT_DIR%
        echo   [2] External  %EXTERNAL_OUTPUT_DIR%
        echo.
        choice /c 12 /n /m "Choose: "
        if errorlevel 2 (set OUTPUT_DIR=%EXTERNAL_OUTPUT_DIR%) else (set OUTPUT_DIR=%DEFAULT_OUTPUT_DIR%)
    )
)

if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

echo.
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
