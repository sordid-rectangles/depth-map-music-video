@echo off
:: -------------------------------------------------------
:: MACHINE SETUP  (a tech should verify this once per PC)
:: -------------------------------------------------------
set K4A_RECORDER=C:\Program Files\Azure Kinect SDK v1.4.1\tools\k4arecorder.exe

:: Where recordings are saved.  Folder is created automatically if missing.
set OUTPUT_DIR=%USERPROFILE%\Desktop\kinect-recordings

:: -------------------------------------------------------
:: RECORDING SETTINGS  (use configure.bat to change these)
:: -------------------------------------------------------
set COLOR_MODE=1440p
set DEPTH_MODE=WFOV_2X2BINNED
set FRAME_RATE=30
set IMU=OFF
