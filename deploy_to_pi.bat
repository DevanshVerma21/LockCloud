@echo off
REM Raspberry Pi Door Lock System - Windows Deployment Helper
REM This script helps you deploy files to your Raspberry Pi from Windows

echo ==========================================
echo Raspberry Pi Door Lock - Deploy to Pi
echo ==========================================
echo.

REM Check if required files exist
if not exist raspberry_pi_door_lock.py (
    echo Error: raspberry_pi_door_lock.py not found!
    pause
    exit /b 1
)

if not exist requirements_pi.txt (
    echo Error: requirements_pi.txt not found!
    pause
    exit /b 1
)

echo Required files found
echo.

REM Get Raspberry Pi connection details
set /p PI_USER="Enter Raspberry Pi username (default: pi): "
if "%PI_USER%"=="" set PI_USER=pi

set /p PI_HOST="Enter Raspberry Pi IP address: "
if "%PI_HOST%"=="" (
    echo Error: IP address is required!
    pause
    exit /b 1
)

echo.
echo Deploying files to %PI_USER%@%PI_HOST%...
echo.

REM Create directory on Pi
echo Creating directory on Raspberry Pi...
ssh %PI_USER%@%PI_HOST% "mkdir -p ~/door_lock"

REM Copy files using scp
echo Copying files...
scp raspberry_pi_door_lock.py %PI_USER%@%PI_HOST%:~/door_lock/
scp requirements_pi.txt %PI_USER%@%PI_HOST%:~/door_lock/
scp install_pi.sh %PI_USER%@%PI_HOST%:~/door_lock/
scp door_lock.service %PI_USER%@%PI_HOST%:~/door_lock/

echo.
echo ==========================================
echo Files deployed successfully!
echo ==========================================
echo.
echo Next steps:
echo 1. Connect to your Raspberry Pi:
echo    ssh %PI_USER%@%PI_HOST%
echo.
echo 2. Navigate to the door_lock directory:
echo    cd ~/door_lock
echo.
echo 3. Run the installation script:
echo    sudo bash install_pi.sh
echo.
echo 4. Test the system:
echo    sudo python3 raspberry_pi_door_lock.py
echo.
pause
