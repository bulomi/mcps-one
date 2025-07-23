@echo off
setlocal

echo ========================================
echo MCPS.ONE Startup Script (Windows)
echo ========================================
echo.

:: Check project structure
if not exist "backend" (
    echo [ERROR] Backend directory not found. Please run from project root.
    pause
    exit /b 1
)
if not exist "frontend" (
    echo [ERROR] Frontend directory not found. Please run from project root.
    pause
    exit /b 1
)
echo [INFO] Project structure OK

:: Check Python
call python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Please install Python 3.8+
    pause
    exit /b 1
)
echo [INFO] Python OK

:: Check Node.js
call node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found. Please install Node.js 16+
    pause
    exit /b 1
)
echo [INFO] Node.js OK

:: Check npm
call npm --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] npm not found
    pause
    exit /b 1
)
echo [INFO] npm OK
echo.

:: Setup backend
echo ========================================
echo Setting up backend...
echo ========================================

:: Install uv if needed
call uv --version >nul 2>&1
if errorlevel 1 (
    echo Installing uv...
    call pip install uv
)

:: Change to backend directory
cd backend

:: Create virtual environment in backend directory
if not exist ".venv" (
    echo Creating virtual environment...
    call uv venv
)

:: Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat

:: Install backend dependencies if needed
if not exist ".venv\pyvenv.cfg" (
    echo Installing Python dependencies...
    call uv pip install -r requirements.txt
) else (
    echo Checking if dependencies need update...
    call uv pip install -r requirements.txt --quiet
)

:: Create data directory if needed
if not exist "data" (
    echo Creating data directory...
    mkdir data
)

:: Initialize database
echo Initializing database...
if not exist "data\mcps.db" (
    echo Creating database and running initial migration...
    call alembic upgrade head
) else (
    echo Checking for database updates...
    call alembic upgrade head
)

:: Start backend
echo Starting backend server...
start "Backend" powershell -NoExit -Command "cd '%~dp0backend'; .venv\Scripts\activate.bat; $env:DISABLE_MCP_AUTO_START='true'; uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

:: Return to project root
cd ..

echo Backend started on http://localhost:8000
echo.

:: Setup frontend
echo ========================================
echo Setting up frontend...
echo ========================================
cd frontend

:: Install dependencies if needed
if not exist "node_modules" (
    echo Installing frontend dependencies...
    call npm install
) else (
    echo Frontend dependencies already installed, skipping...
)

:: Start frontend
echo Starting frontend server...
start "Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo Frontend started on http://localhost:5173
echo.

echo ========================================
echo Startup Complete!
echo ========================================
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo API Docs: http://localhost:8000/docs
echo.
echo Press any key to exit...
pause >nul