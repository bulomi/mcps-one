@echo off
setlocal enabledelayedexpansion

echo ========================================
echo MCPS.ONE Stop Script (Windows)
echo ========================================
echo.

:: Stop Backend
echo [Info] Stopping Backend...
taskkill /f /im cmd.exe /fi "WINDOWTITLE eq Backend*" >nul 2>&1
if errorlevel 1 (
    echo [Warning] Backend window not found or already stopped
) else (
    echo [Success] Backend stopped
)

:: Stop Frontend
echo [Info] Stopping Frontend...
taskkill /f /im cmd.exe /fi "WINDOWTITLE eq Frontend*" >nul 2>&1
if errorlevel 1 (
    echo [Warning] Frontend window not found or already stopped
) else (
    echo [Success] Frontend stopped
)

:: Clean up other possible processes
echo [Info] Cleaning up other related processes...

:: Stop possible uvicorn processes
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo csv ^| findstr "uvicorn"') do (
    echo [Info] Found uvicorn process, stopping...
    taskkill /f /pid %%i >nul 2>&1
)

:: Stop possible node processes (carefully, only stop dev server related)
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq node.exe" /fo csv ^| findstr "vite"') do (
    echo [Info] Found Vite dev server process, stopping...
    taskkill /f /pid %%i >nul 2>&1
)

:: Stop port occupied processes
echo [Info] Checking and stopping port occupied processes

:: Stop 8000 port processes (Backend)
for /f "tokens=5" %%i in ('netstat -ano ^| findstr ":8000"') do (
    if not "%%i"=="" (
        echo [Info] Stopping process occupying port 8000 (PID: %%i)
        taskkill /f /pid %%i >nul 2>&1
    )
)

:: Stop 5173 port processes (Frontend) 
for /f "tokens=5" %%i in ('netstat -ano ^| findstr ":5173"') do (
    if not "%%i"=="" (
        echo [Info] Stopping process occupying port 5173 (PID: %%i)
        taskkill /f /pid %%i >nul 2>&1
    )
)

echo.
echo [Success] All services stopped
echo.
echo Press any key to exit...
pause >nul