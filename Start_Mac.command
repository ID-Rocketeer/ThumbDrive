#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

if [ -f "./server_bin/server_mac" ]; then
    chmod +x ./server_bin/server_mac
    ./server_bin/server_mac &
elif [ -f "./thumbdrive_runner.py" ]; then
    echo "[ThumbDrive] Launching python thumbdrive_runner.py..."
    python3 ./thumbdrive_runner.py
else
    echo "==================================================================="
    echo "ERROR: ./server_bin/server_mac was not found!"
    echo "==================================================================="
    read -p "Press Enter to exit..."
fi
