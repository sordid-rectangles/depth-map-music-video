@echo off
:: -------------------------------------------------------
:: MACHINE SETUP  (a tech should verify this once per PC)
:: -------------------------------------------------------
set K4A_RECORDER=C:\Program Files\Azure Kinect SDK v1.4.1\tools\k4arecorder.exe

:: -------------------------------------------------------
:: RECORDING SETTINGS  (use configure.bat to change these)
:: -------------------------------------------------------
set PRESET_NAME=Primary
set COLOR_MODE=1440p
set DEPTH_MODE=WFOV_2X2BINNED
set FRAME_RATE=30
set IMU=OFF
