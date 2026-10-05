#!/bin/bash
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
cd "$SCRIPT_DIR"

if [ -f "./server_bin/server_linux" ]; then
    chmod +x ./server_bin/server_linux
    ./server_bin/server_linux &
elif [ -f "./thumbdrive_runner.py" ]; then
    echo "[ThumbDrive] Launching python thumbdrive_runner.py..."
    python3 ./thumbdrive_runner.py
else
    echo "==================================================================="
    echo "ERROR: ./server_bin/server_linux was not found!"
    echo "==================================================================="
    read -p "Press Enter to exit..."
fi
