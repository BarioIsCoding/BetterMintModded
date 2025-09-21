#!/bin/bash

# BetterMint Modded v3.0.0 Startup Script
echo -ne "\033]0;BetterMint Modded - Server Startup\007"

echo
echo "==============================================="
echo "    BetterMint Modded v3.0.0 - Server Setup"
echo "==============================================="
echo

# Change to script directory
cd "$(dirname "$0")"

# Check if Python is installed
if ! python3 --version >/dev/null 2>&1; then
    echo "ERROR: Python is not installed or not in PATH"
    echo "Please install Python 3.8 or higher"
    echo "Ubuntu/Debian: sudo apt install python3 python3-pip python3-venv"
    echo "CentOS/RHEL: sudo yum install python3 python3-pip"
    echo "Arch: sudo pacman -S python python-pip"
    echo
    read -p "Press any key to exit..."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo "Python version: $PYTHON_VERSION"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        read -p "Press any key to exit..."
        exit 1
    fi
    echo "Virtual environment created successfully."
    echo
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment"
    read -p "Press any key to exit..."
    exit 1
fi

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip --quiet

# Install/update dependencies
echo "Installing dependencies from requirements.txt..."
python -m pip install -r requirements.txt --quiet
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    echo "Make sure requirements.txt exists and is valid"
    read -p "Press any key to exit..."
    exit 1
fi

# Check for engines directory
if [ ! -d "engines" ]; then
    echo "WARNING: engines/ directory not found"
    echo "Please ensure you have the chess engines installed"
    echo
fi

# Check for Stockfish
if [ -f "engines/stockfish/stockfish" ]; then
    echo "✓ Stockfish engine found"
else
    echo "⚠ Stockfish engine not found at engines/stockfish/stockfish"
fi

# Check for Leela
if [ -f "engines/leela/lc0" ]; then
    echo "✓ Leela Chess Zero engine found"
else
    echo "⚠ Leela Chess Zero engine not found at engines/leela/lc0"
fi

# Check for Maia weights
if [ -d "weights" ]; then
    WEIGHT_COUNT=$(ls weights/maia-*.pb.gz 2>/dev/null | wc -l)
    if [ "$WEIGHT_COUNT" -gt 0 ]; then
        echo "✓ Found $WEIGHT_COUNT Maia weight files"
    else
        echo "⚠ No Maia weight files found in weights/ directory"
    fi
else
    echo "⚠ weights/ directory not found"
fi

# Check for opening books
if [ -d "books" ]; then
    BOOK_COUNT=$(ls books/*.{bin,abk,ctg,book} 2>/dev/null | wc -l)
    if [ "$BOOK_COUNT" -gt 0 ]; then
        echo "✓ Found $BOOK_COUNT opening book files"
    else
        echo "⚠ No opening book files found in books/ directory"
    fi
else
    echo "⚠ books/ directory not found"
fi

# Check for tablebases
if [ -d "tablebases" ]; then
    TB_COUNT=$(find tablebases -name "*.rtbw" -o -name "*.rtbz" 2>/dev/null | wc -l)
    if [ "$TB_COUNT" -gt 0 ]; then
        echo "✓ Found $TB_COUNT tablebase files"
    else
        echo "⚠ No Syzygy tablebase files found in tablebases/ directory"
    fi
else
    echo "⚠ tablebases/ directory not found"
fi

echo
echo "==============================================="
echo "    Starting BetterMint Modded Server"
echo "==============================================="
echo
echo "The GUI application will open shortly..."
echo "Use the GUI to configure engines and start the server."
echo
echo "WebSocket will be available at: ws://localhost:8000/ws"
echo "Web interface will be available at: http://localhost:8000"
echo
echo "Press Ctrl+C to stop the server when running."
echo

# Start the GUI application
echo "Starting BetterMint Modded GUI..."
python main.py

# Check exit code
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo
    echo "ERROR: Application exited with error code $EXIT_CODE"
    echo "Check the error messages above for details."
    echo
else
    echo
    echo "BetterMint Modded server has been stopped."
    echo
fi

# Deactivate virtual environment
deactivate

echo "Press any key to exit..."
read -n 1 -s
exit $EXIT_CODE