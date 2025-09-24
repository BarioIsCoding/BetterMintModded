@echo off
setlocal enabledelayedexpansion

:: BetterMint Modded v3.0.0 Startup Script
title BetterMint Modded - Server Startup

echo.
echo ===============================================
echo    BetterMint Modded v3.0.0 - Server Setup
echo ===============================================
echo.

:: Change to script directory
cd /d "%~dp0"
echo "%~dp0"
:: Check if Python is installed
python --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://python.org
    echo.
    pause
    exit /b 1
)

:: Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python version: %PYTHON_VERSION%

:: Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully.
    echo.
)

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

:: Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip --quiet

:: Install/update dependencies
echo Installing dependencies from requirements.txt...
python -m pip install -r requirements.txt --quiet
if %ERRORLEVEL% neq 0 (
    echo ERROR: Failed to install dependencies
    echo Make sure requirements.txt exists and is valid
    pause
    exit /b 1
)

:: Check for engines directory
if not exist "engines" (
    echo WARNING: engines/ directory not found
    echo Please ensure you have the chess engines installed
    echo.
)

:: Check for Stockfish
if exist "engines\stockfish\stockfish.exe" (
    echo ✓ Stockfish engine found
) else (
    echo ⚠ Stockfish engine not found at engines\stockfish\stockfish.exe
)

:: Check for Leela
if exist "engines\leela\lc0.exe" (
    echo ✓ Leela Chess Zero engine found
) else (
    echo ⚠ Leela Chess Zero engine not found at engines\leela\lc0.exe
)

:: Check for Maia weights
if exist "weights" (
    set WEIGHT_COUNT=0
    for %%f in (weights\maia-*.pb.gz) do set /a WEIGHT_COUNT+=1
    if !WEIGHT_COUNT! gtr 0 (
        echo ✓ Found !WEIGHT_COUNT! Maia weight files
    ) else (
        echo ⚠ No Maia weight files found in weights/ directory
    )
) else (
    echo ⚠ weights/ directory not found
)

:: Check for opening books
if exist "books" (
    set BOOK_COUNT=0
    for %%f in (books\*.bin books\*.abk books\*.ctg books\*.book) do set /a BOOK_COUNT+=1
    if !BOOK_COUNT! gtr 0 (
        echo ✓ Found !BOOK_COUNT! opening book files
    ) else (
        echo ⚠ No opening book files found in books/ directory
    )
) else (
    echo ⚠ books/ directory not found
)

:: Check for tablebases
if exist "tablebases" (
    set TB_COUNT=0
    for /r tablebases %%f in (*.rtbw *.rtbz) do set /a TB_COUNT+=1
    if !TB_COUNT! gtr 0 (
        echo ✓ Found !TB_COUNT! tablebase files
    ) else (
        echo ⚠ No Syzygy tablebase files found in tablebases/ directory
    )
) else (
    echo ⚠ tablebases/ directory not found
)

echo.
echo ===============================================
echo    Starting BetterMint Modded Server
echo ===============================================
echo.
echo The GUI application will open shortly...
echo Use the GUI to configure engines and start the server.
echo.
echo WebSocket will be available at: ws://localhost:8000/ws
echo Web interface will be available at: http://localhost:8000
echo.
echo Press Ctrl+C to stop the server when running.
echo.

:: Start the GUI application
echo Installing Playwright...
playwright install
echo Starting GUI... If this gets stuck, open a ticket on GitHub.
python main.py

:: Check exit code
if %ERRORLEVEL% neq 0 (
    echo.
    echo ERROR: Application exited with error code %ERRORLEVEL%
    echo Check the error messages above for details.
    echo.
) else (
    echo.
    echo BetterMint Modded server has been stopped.
    echo.
)

echo Press any key to exit...
pause >nul
exit /b 0
