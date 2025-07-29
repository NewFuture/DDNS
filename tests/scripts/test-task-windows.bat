@echo off
REM Windows Task Management Test Script
REM Tests DDNS task functionality on Windows systems
REM Exits with non-zero status on verification failure
REM Usage: test-task-windows.bat [DDNS_COMMAND]
REM Examples:
REM   test-task-windows.bat                    (uses default: python3 -m ddns)
REM   test-task-windows.bat ddns               (uses ddns command)
REM   test-task-windows.bat ./dist/ddns.exe    (uses binary executable)
REM   test-task-windows.bat "python -m ddns"   (uses custom python command)

setlocal enabledelayedexpansion
set "PYTHON_CMD=python3"

REM Check if DDNS command is provided as argument
if "%~1"=="" (
    set "DDNS_CMD=%PYTHON_CMD% -m ddns"
) else (
    set "DDNS_CMD=%~1"
)

echo === DDNS Task Management Test for Windows ===
echo DDNS Command: %DDNS_CMD%
echo.

REM Check if we're actually on Windows
ver | findstr /i "Windows" >nul
if !ERRORLEVEL! neq 0 (
    echo ERROR: This script is designed for Windows
    exit /b 1
)

for /f "tokens=*" %%i in ('ver') do echo Confirmed running on %%i

REM Test Step 1: Initial state check
echo.
echo === Step 1: Initial state verification ===
%DDNS_CMD% task -h
if !ERRORLEVEL! neq 0 (
    echo ERROR: Task help command failed
    exit /b 1
)

%DDNS_CMD% task --status
for /f "tokens=*" %%i in ('%DDNS_CMD% task --status ^| findstr "Installed:"') do set "initial_status=%%i"
if not defined initial_status set "initial_status=Installed: Unknown"
echo Initial status: !initial_status!

REM Check initial system state - should not exist
echo.
echo === Step 2: Initial system state verification ===
echo Checking Windows Task Scheduler...
schtasks /query /tn "DDNS" >nul 2>&1
if !ERRORLEVEL! == 0 (
    echo ERROR: DDNS scheduled task should not exist initially but was found
    exit /b 1
) else (
    echo OK: No DDNS scheduled task found initially
)

REM Test Step 3: Install task
echo.
echo === Step 3: Installing DDNS task ===
echo !initial_status! | findstr /i "Installed.*No" >nul
if !ERRORLEVEL! == 0 (
    echo Installing task with 12-minute interval...
    %DDNS_CMD% task --install 12
    if !ERRORLEVEL! neq 0 (
        echo ERROR: Task installation failed
        exit /b 1
    )
    echo OK: Task installation command completed
) else (
    echo Task already installed, proceeding with verification...
)

REM Test Step 4: Verify installation
echo.
echo === Step 4: Verifying installation ===
for /f "tokens=*" %%i in ('%DDNS_CMD% task --status ^| findstr "Installed:"') do set "install_status=%%i"
echo Status: !install_status!

echo !install_status! | findstr /i "Installed.*Yes" >nul
if !ERRORLEVEL! == 0 (
    echo OK: DDNS status verification passed
) else (
    echo ERROR: Expected 'Installed: Yes', got '!install_status!'
    exit /b 1
)

REM Check system state after installation
echo.
echo === Step 5: System verification after installation ===
echo Checking Windows Task Scheduler...
schtasks /query /tn "DDNS" >nul 2>&1
if !ERRORLEVEL! == 0 (
    echo OK: DDNS scheduled task found
    echo Task details:
    schtasks /query /tn "DDNS" /fo list 2>nul | findstr /i "TaskName State"
) else (
    echo ERROR: Scheduled task should exist but was not found
    exit /b 1
)

REM Test Step 6: Delete task
echo.
echo === Step 6: Deleting DDNS task ===
%DDNS_CMD% task --delete
if !ERRORLEVEL! neq 0 (
    echo ERROR: Task deletion failed
    exit /b 1
)
echo OK: Task deletion command completed

REM Test Step 7: Verify deletion
echo.
echo === Step 7: Verifying deletion ===
for /f "tokens=*" %%i in ('%DDNS_CMD% task --status ^| findstr "Installed:"') do set "final_status=%%i"
echo Status: !final_status!

echo !final_status! | findstr /i "Installed.*No" >nul
if !ERRORLEVEL! == 0 (
    echo OK: DDNS status verification passed
) else (
    echo ERROR: Expected 'Installed: No', got '!final_status!'
    exit /b 1
)

REM Final system state verification
echo.
echo === Step 8: Final system state verification ===
echo Checking Windows Task Scheduler...
schtasks /query /tn "DDNS" >nul 2>&1
if !ERRORLEVEL! == 0 (
    echo ERROR: Scheduled task should not exist but was found
    exit /b 1
) else (
    echo OK: DDNS scheduled task successfully removed
)

REM Test help commands availability
echo.
echo === Step 9: Help commands verification ===
%DDNS_CMD% task --help | findstr /i "install uninstall enable disable status" >nul
if !ERRORLEVEL! == 0 (
    echo OK: Task commands found in help
) else (
    echo ERROR: Task commands missing from help
    exit /b 1
)

echo.
echo ===============================================
echo ALL TESTS PASSED - Windows task management OK
echo ===============================================
echo.

exit /b 0
