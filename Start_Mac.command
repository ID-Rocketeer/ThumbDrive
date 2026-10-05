#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"
chmod +x ./server_bin/server_mac
./server_bin/server_mac &
