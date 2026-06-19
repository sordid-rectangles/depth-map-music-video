@echo off
setlocal enabledelayedexpansion
call "%~dp0config.bat"
set CONFIG_FILE=%~dp0config.bat

:MAIN_MENU
cls
echo ============================================================
echo   KINECT RECORDING CONFIGURATION
echo ============================================================
echo.
echo   Active preset : %PRESET_NAME%
echo   Color         : %COLOR_MODE%
echo   Depth         : %DEPTH_MODE%
echo   Frame rate    : %FRAME_RATE% fps
echo   IMU sensor    : %IMU%
echo.
echo   --- Presets (all wide-angle, 30 fps) ---
echo   1.  Primary        1440p (2K) color  +  WFOV 2x2 binned depth  *default*
echo   2.  Hero Shot      2160p (4K) color  +  WFOV 2x2 binned depth
echo   3.  Long Take      1080p color       +  WFOV 2x2 binned depth  (smaller files)
echo   4.  Depth Ref      no color          +  WFOV 2x2 binned depth  (VFX/comp pass)
echo.
echo   5.  Toggle IMU sensor (currently: %IMU%)
echo.
echo   S.  Save and exit
echo   X.  Exit without saving
echo.
choice /c 12345SX /n /m "Choose: "

if errorlevel 7 goto EXIT_NOSAVE
if errorlevel 6 goto SAVE
if errorlevel 5 goto TOGGLE_IMU
if errorlevel 4 goto PRESET_DEPTH_REF
if errorlevel 3 goto PRESET_LONG_TAKE
if errorlevel 2 goto PRESET_HERO
if errorlevel 1 goto PRESET_PRIMARY


:PRESET_PRIMARY
set PRESET_NAME=Primary
set COLOR_MODE=1440p
set DEPTH_MODE=WFOV_2X2BINNED
set FRAME_RATE=30
goto MAIN_MENU

:PRESET_HERO
set PRESET_NAME=Hero Shot
set COLOR_MODE=2160p
set DEPTH_MODE=WFOV_2X2BINNED
set FRAME_RATE=30
goto MAIN_MENU

:PRESET_LONG_TAKE
set PRESET_NAME=Long Take
set COLOR_MODE=1080p
set DEPTH_MODE=WFOV_2X2BINNED
set FRAME_RATE=30
goto MAIN_MENU

:PRESET_DEPTH_REF
set PRESET_NAME=Depth Ref
set COLOR_MODE=OFF
set DEPTH_MODE=WFOV_2X2BINNED
set FRAME_RATE=30
goto MAIN_MENU

:TOGGLE_IMU
if "%IMU%"=="OFF" (set IMU=ON) else (set IMU=OFF)
goto MAIN_MENU


:SAVE
echo @echo off > "%CONFIG_FILE%"
echo :: ------------------------------------------------------- >> "%CONFIG_FILE%"
echo :: MACHINE SETUP  (a tech should verify this once per PC) >> "%CONFIG_FILE%"
echo :: ------------------------------------------------------- >> "%CONFIG_FILE%"
echo set K4A_RECORDER=%K4A_RECORDER% >> "%CONFIG_FILE%"
echo. >> "%CONFIG_FILE%"
echo :: ------------------------------------------------------- >> "%CONFIG_FILE%"
echo :: RECORDING SETTINGS  (use configure.bat to change these) >> "%CONFIG_FILE%"
echo :: ------------------------------------------------------- >> "%CONFIG_FILE%"
echo set PRESET_NAME=%PRESET_NAME% >> "%CONFIG_FILE%"
echo set COLOR_MODE=%COLOR_MODE% >> "%CONFIG_FILE%"
echo set DEPTH_MODE=%DEPTH_MODE% >> "%CONFIG_FILE%"
echo set FRAME_RATE=%FRAME_RATE% >> "%CONFIG_FILE%"
echo set IMU=%IMU% >> "%CONFIG_FILE%"

echo.
echo Settings saved.
echo.
pause
exit /b 0


:EXIT_NOSAVE
echo.
echo Exiting without saving.
echo.
exit /b 0
