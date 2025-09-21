@echo off
setlocal enabledelayedexpansion

title BetterMint Pip Fix Script

:START
cls
echo ===============================================
echo    BetterMint Pip Fix Script
echo ===============================================
echo.

:: Change to script directory
echo [Step 1] Changing to script directory...
cd /d "%~dp0"
echo Current directory: %CD%
echo.

:: Navigate to parent folder (EngineWS)
echo [Step 2] Navigating to EngineWS directory...
cd ..
if %ERRORLEVEL% neq 0 (
    echo ERROR: Could not navigate to parent directory
    echo.
    goto ERROR_RESTART
)
echo Current directory: %CD%
echo.

:: Delete venv folder
echo [Step 3] Deleting venv folder...
if exist "venv" (
    echo Found venv folder, deleting...
    rmdir /s /q "venv" 2>nul
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Failed to delete venv folder
        echo The folder may be in use or access denied.
        echo.
        goto ERROR_RESTART
    )
    :: Double-check deletion
    if exist "venv" (
        echo ERROR: venv folder still exists after deletion
        echo.
        goto ERROR_RESTART
    )
    echo ✓ venv folder deleted successfully
) else (
    echo ✓ venv folder not found (already clean)
)

echo.
echo ===============================================
echo    Cleanup Complete!
echo ===============================================
echo.
echo Virtual environment has been cleaned up.
echo.
set /p "START_AGAIN=Do you want to start BetterMint Modded now? (y/N): "
if /i "!START_AGAIN!"=="y" (
    echo.
    echo Starting BetterMint Modded...
    echo.
    
    :: Check if RunUnix.sh exists
    if exist "RunUnix.sh" (
        echo Found RunUnix.sh, starting BetterMint Modded...
        echo Current directory: %CD%
        echo.
        call "RunUnix.sh"
    ) else (
        echo ERROR: RunUnix.sh not found in %CD%
        echo Please manually navigate to the EngineWS directory and run RunUnix.sh
        echo.
        pause
    )
) else (
    echo.
    echo BetterMint Modded was not started.
    echo You can manually start it later by running RunWindows.bat in the EngineWS directory.
    echo.
    pause
)
exit /b 0

:ERROR_RESTART
echo ===============================================
echo    ERROR OCCURRED - RESTARTING
echo ===============================================
echo.
echo File deletion failed. This usually happens when:
echo - BetterMintModded is still running
echo - Files are being used by another process
echo - Insufficient permissions
echo.
echo Please make sure BetterMintModded is completely closed
echo and try again.
echo.
pause
goto START