#!/bin/bash
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
cd "$SCRIPT_DIR"
chmod +x ./server_bin/server_linux
./server_bin/server_linux &
