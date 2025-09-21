@echo off
setlocal enabledelayedexpansion

title BetterMint Playwright Fix Script

:START
cls
echo ===============================================
echo    BetterMint Playwright Fix Script
echo ===============================================
echo.
echo IMPORTANT: Please fully close BetterMintModded before proceeding.
echo This script will clean up browser profile and storage folders.
echo.
pause
echo.

:: Step 2: Change to script directory
echo [Step 2] Changing to script directory...
cd /d "%~dp0"
echo Current directory: %CD%
echo.

:: Step 3: Navigate to parent folder 3 times (BetterMint root)
echo [Step 3] Navigating to BetterMint root directory...
cd ..
cd ..
cd ..
echo Current directory: %CD%
echo.

:: Step 4: Securely delete chrome_profile folder
echo [Step 4] Deleting chrome_profile folder...
if exist "chrome_profile" (
    echo Found chrome_profile folder, deleting...
    rmdir /s /q "chrome_profile" 2>nul
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Failed to delete chrome_profile folder
        echo The folder may be in use or access denied.
        echo.
        goto ERROR_RESTART
    )
    :: Double-check deletion
    if exist "chrome_profile" (
        echo ERROR: chrome_profile folder still exists after deletion
        echo.
        goto ERROR_RESTART
    )
    echo ✓ chrome_profile folder deleted successfully
) else (
    echo ✓ chrome_profile folder not found (already clean)
)
echo.

:: Step 5: Navigate to EngineWS folder (back 2 levels from BetterMint)
echo [Step 5] Navigating to EngineWS directory...
cd EngineWS
if %ERRORLEVEL% neq 0 (
    echo ERROR: Could not find EngineWS directory
    echo.
    goto ERROR_RESTART
)
echo Current directory: %CD%
echo.

:: Step 6: Delete webview storage folders
echo [Step 6] Deleting webview storage folders...

:: Delete webview_storage folder
if exist "webview_storage" (
    echo Found webview_storage folder, deleting...
    rmdir /s /q "webview_storage" 2>nul
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Failed to delete webview_storage folder
        echo.
        goto ERROR_RESTART
    )
    :: Double-check deletion
    if exist "webview_storage" (
        echo ERROR: webview_storage folder still exists after deletion
        echo.
        goto ERROR_RESTART
    )
    echo ✓ webview_storage folder deleted successfully
) else (
    echo ✓ webview_storage folder not found (already clean)
)

:: Delete webview_streaming folder
if exist "webview_streaming" (
    echo Found webview_streaming folder, deleting...
    rmdir /s /q "webview_streaming" 2>nul
    if %ERRORLEVEL% neq 0 (
        echo ERROR: Failed to delete webview_streaming folder
        echo.
        goto ERROR_RESTART
    )
    :: Double-check deletion
    if exist "webview_streaming" (
        echo ERROR: webview_streaming folder still exists after deletion
        echo.
        goto ERROR_RESTART
    )
    echo ✓ webview_streaming folder deleted successfully
) else (
    echo ✓ webview_streaming folder not found (already clean)
)

echo.
echo ===============================================
echo    Cleanup Complete!
echo ===============================================
echo.
echo All browser profile and storage folders have been cleaned up.
echo.
set /p "START_AGAIN=Do you want to start BetterMint Modded now? (y/N): "
if /i "!START_AGAIN!"=="y" (
    echo.
    echo Starting BetterMint Modded...
    echo.
    
    :: Navigate back to script directory
    cd /d "%~dp0"
    
    :: Go up 2 directories to EngineWS
    cd ..
    cd ..
    
    :: Check if Run.bat exists
    if exist "Run.bat" (
        echo Found Run.bat, starting BetterMint Modded...
        echo Current directory: %CD%
        echo.
        call "Run.bat"
    ) else (
        echo ERROR: Run.bat not found in %CD%
        echo Please manually navigate to the EngineWS directory and run Run.bat
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