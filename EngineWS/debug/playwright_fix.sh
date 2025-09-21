#!/bin/bash

echo -ne "\033]0;BetterMint Pip Fix Script\007"

START() {
    clear
    echo "==============================================="
    echo "    BetterMint Pip Fix Script"
    echo "==============================================="
    echo

    # Step 1: Change to script directory
    echo "[Step 1] Changing to script directory..."
    cd "$(dirname "$0")"
    echo "Current directory: $(pwd)"
    echo

    # Step 2: Navigate to parent folder (EngineWS)
    echo "[Step 2] Navigating to EngineWS directory..."
    cd ..
    if [ $? -ne 0 ]; then
        echo "ERROR: Could not navigate to parent directory"
        echo
        ERROR_RESTART
        return
    fi
    echo "Current directory: $(pwd)"
    echo

    # Step 3: Delete venv folder
    echo "[Step 3] Deleting venv folder..."
    if [ -d "venv" ]; then
        echo "Found venv folder, deleting..."
        rm -rf "venv" 2>/dev/null
        if [ $? -ne 0 ]; then
            echo "ERROR: Failed to delete venv folder"
            echo "The folder may be in use or access denied."
            echo
            ERROR_RESTART
            return
        fi
        # Double-check deletion
        if [ -d "venv" ]; then
            echo "ERROR: venv folder still exists after deletion"
            echo
            ERROR_RESTART
            return
        fi
        echo "✓ venv folder deleted successfully"
    else
        echo "✓ venv folder not found (already clean)"
    fi

    echo
    echo "==============================================="
    echo "    Cleanup Complete!"
    echo "==============================================="
    echo
    echo "Virtual environment has been cleaned up."
    echo
    read -p "Do you want to start BetterMint Modded now? (y/N): " START_AGAIN
    if [[ "$START_AGAIN" =~ ^[Yy]$ ]]; then
        echo
        echo "Starting BetterMint Modded..."
        echo
        
        # Check if RunUnix.sh exists
        if [ -f "RunUnix.sh" ]; then
            echo "Found RunUnix.sh, starting BetterMint Modded..."
            echo "Current directory: $(pwd)"
            echo
            bash "RunUnix.sh"
        else
            echo "ERROR: RunUnix.sh not found in $(pwd)"
            echo "Please manually navigate to the EngineWS directory and run RunUnix.sh"
            echo
            read -p "Press any key to continue..."
        fi
    else
        echo
        echo "BetterMint Modded was not started."
        echo "You can manually start it later by running RunUnix.sh in the EngineWS directory."
        echo
        read -p "Press any key to continue..."
    fi
    exit 0
}

ERROR_RESTART() {
    echo "==============================================="
    echo "    ERROR OCCURRED - RESTARTING"
    echo "==============================================="
    echo
    echo "File deletion failed. This usually happens when:"
    echo "- BetterMintModded is still running"
    echo "- Files are being used by another process"
    echo "- Insufficient permissions"
    echo
    echo "Please make sure BetterMintModded is completely closed"
    echo "and try again."
    echo
    read -p "Press any key to continue..."
    START
}

# Start the script
START