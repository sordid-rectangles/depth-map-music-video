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
echo   1.  Output folder  :  %OUTPUT_DIR%
echo   2.  Color mode     :  %COLOR_MODE%
echo   3.  Depth mode     :  %DEPTH_MODE%
echo   4.  Frame rate     :  %FRAME_RATE% fps
echo   5.  IMU sensor     :  %IMU%
echo.
echo   S.  Save and exit
echo   X.  Exit without saving
echo.
choice /c 12345SX /n /m "Choose a number to change it, or S to save: "

if errorlevel 7 goto EXIT_NOSAVE
if errorlevel 6 goto SAVE
if errorlevel 5 goto SET_IMU
if errorlevel 4 goto SET_RATE
if errorlevel 3 goto SET_DEPTH
if errorlevel 2 goto SET_COLOR
if errorlevel 1 goto SET_OUTPUT


:SET_OUTPUT
cls
echo ============================================================
echo   OUTPUT FOLDER
echo ============================================================
echo.
echo   Current: %OUTPUT_DIR%
echo.
echo   Type a new folder path and press Enter.
echo   (Leave blank to keep current setting.)
echo.
set /p NEW_DIR="  New folder: "
if not "%NEW_DIR%"=="" set OUTPUT_DIR=%NEW_DIR%
goto MAIN_MENU


:SET_COLOR
cls
echo ============================================================
echo   COLOR MODE
echo ============================================================
echo.
echo   1.  3072p    (4:3,  4K+,  max 15 fps)
echo   2.  2160p    (16:9, 4K,   max 30 fps)
echo   3.  1440p    (16:9,       max 30 fps)  *recommended*
echo   4.  1080p    (16:9,       max 30 fps)
echo   5.  720p     (16:9,       max 30 fps)
echo   6.  OFF      (no color stream)
echo.
echo   Current: %COLOR_MODE%
echo.
choice /c 123456 /n /m "Choose: "

if errorlevel 6 set COLOR_MODE=OFF
if errorlevel 5 if not errorlevel 6 set COLOR_MODE=720p
if errorlevel 4 if not errorlevel 5 set COLOR_MODE=1080p
if errorlevel 3 if not errorlevel 4 set COLOR_MODE=1440p
if errorlevel 2 if not errorlevel 3 set COLOR_MODE=2160p
if errorlevel 1 if not errorlevel 2 set COLOR_MODE=3072p
goto MAIN_MENU


:SET_DEPTH
cls
echo ============================================================
echo   DEPTH MODE
echo ============================================================
echo.
echo   1.  WFOV 2x2 Binned   Wide angle, binned    (up to 30 fps)  *recommended*
echo   2.  WFOV Full Res     Wide angle, full res  (up to 15 fps)
echo   3.  NFOV Unbinned     Narrow angle, full res (up to 30 fps)
echo   4.  NFOV 2x2 Binned   Narrow angle, binned  (up to 30 fps)
echo   5.  Passive IR        IR only, no depth
echo   6.  OFF               No depth stream
echo.
echo   Current: %DEPTH_MODE%
echo.
choice /c 123456 /n /m "Choose: "

if errorlevel 6 set DEPTH_MODE=OFF
if errorlevel 5 if not errorlevel 6 set DEPTH_MODE=PASSIVE_IR
if errorlevel 4 if not errorlevel 5 set DEPTH_MODE=NFOV_2X2BINNED
if errorlevel 3 if not errorlevel 4 set DEPTH_MODE=NFOV_UNBINNED
if errorlevel 2 if not errorlevel 3 set DEPTH_MODE=WFOV_UNBINNED
if errorlevel 1 if not errorlevel 2 set DEPTH_MODE=WFOV_2X2BINNED
goto MAIN_MENU


:SET_RATE
cls
echo ============================================================
echo   FRAME RATE
echo ============================================================
echo.
echo   Note: WFOV Full Res depth mode is limited to 15 fps max.
echo         3072p color is limited to 15 fps max.
echo.
echo   1.  30 fps
echo   2.  15 fps
echo   3.   5 fps
echo.
echo   Current: %FRAME_RATE% fps
echo.
choice /c 123 /n /m "Choose: "

if errorlevel 3 set FRAME_RATE=5
if errorlevel 2 if not errorlevel 3 set FRAME_RATE=15
if errorlevel 1 if not errorlevel 2 set FRAME_RATE=30
goto MAIN_MENU


:SET_IMU
cls
echo ============================================================
echo   IMU SENSOR  (accelerometer + gyroscope)
echo ============================================================
echo.
echo   1.  OFF   (recommended for most shoots)
echo   2.  ON    (records motion data alongside footage)
echo.
echo   Current: %IMU%
echo.
choice /c 12 /n /m "Choose: "

if errorlevel 2 set IMU=ON
if errorlevel 1 if not errorlevel 2 set IMU=OFF
goto MAIN_MENU


:SAVE
echo @echo off                                                           > "%CONFIG_FILE%"
echo :: -------------------------------------------------------         >> "%CONFIG_FILE%"
echo :: MACHINE SETUP  (a tech should verify this once per PC)          >> "%CONFIG_FILE%"
echo :: -------------------------------------------------------         >> "%CONFIG_FILE%"
echo set K4A_RECORDER=%K4A_RECORDER%                                    >> "%CONFIG_FILE%"
echo.                                                                    >> "%CONFIG_FILE%"
echo :: Where recordings are saved.                                      >> "%CONFIG_FILE%"
echo set OUTPUT_DIR=%OUTPUT_DIR%                                         >> "%CONFIG_FILE%"
echo.                                                                    >> "%CONFIG_FILE%"
echo :: -------------------------------------------------------         >> "%CONFIG_FILE%"
echo :: RECORDING SETTINGS  (use configure.bat to change these)         >> "%CONFIG_FILE%"
echo :: -------------------------------------------------------         >> "%CONFIG_FILE%"
echo set COLOR_MODE=%COLOR_MODE%                                         >> "%CONFIG_FILE%"
echo set DEPTH_MODE=%DEPTH_MODE%                                         >> "%CONFIG_FILE%"
echo set FRAME_RATE=%FRAME_RATE%                                         >> "%CONFIG_FILE%"
echo set IMU=%IMU%                                                       >> "%CONFIG_FILE%"

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
