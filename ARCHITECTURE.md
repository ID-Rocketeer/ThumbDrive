# Technical Architecture & Build Specifications

This document outlines the technical design, filesystem constraints, auto-browser launch mechanics, and CI/CD build pipeline for the self-contained portable USB Audio Web Server.

---

## 1. Cross-Platform Filesystem Compatibility

### The exFAT/FAT32 Constraint
USB drives intended for universal compatibility must be formatted with **exFAT** or **FAT32**. 
* Neither format supports standard POSIX symbolic links.
* Windows NTFS symbolic links require Administrator privileges or Developer Mode.

### PaperHanger Symlink Replacement
Instead of pointing a symlink `wallpaper.webp` -> `target_image.webp`, `PaperHanger` uses a lightweight JSON state file (`current_wallpaper.json`):

```json
{
  "active_wallpaper": "halloween_night.webp",
  "palette_override": null,
  "updated_at": 1791145900
}
```

#### HTTP Endpoint Handler Logic:
1. When `/wallpaper` is requested, the audio server reads `current_wallpaper.json`.
2. The server constructs the relative file path `wallpapers/<active_wallpaper>`.
3. If the file exists, it serves the image binary directly.
4. If missing, it falls back to a default image in `wallpapers/`.

This pattern avoids all OS permission and filesystem symlink limitations.

---

## 2. Automatic Web Browser Launching

Because modern operating systems disable `autorun.inf` execution for security reasons, the root launcher scripts invoke the standalone server executable.

### In-Process Auto-Launch Sequence
The server executable handles launching the web browser automatically upon successful HTTP socket bind:

```python
import sys
import time
import threading
import webbrowser
from audio_server.server import run_server

def launch_browser(port):
    time.sleep(0.8)  # Wait for socket initialization
    webbrowser.open(f"http://127.0.0.1:{port}")

if __name__ == "__main__":
    port = 5000
    threading.Thread(target=launch_browser, args=(port,), daemon=True).start()
    run_server(port=port)
```

---

## 3. Cross-Platform Launcher Scripts

### Windows (`Start_Windows.bat`)
```batch
@echo off
title ThumbDrive Audio Server
cd /d "%~dp0"
start "" "server_bin\server_win.exe"
```

### macOS (`Start_Mac.command`)
```bash
#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"
chmod +x ./server_bin/server_mac
./server_bin/server_mac &
```

### Linux (`Start_Linux.sh`)
```bash
#!/bin/bash
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
cd "$SCRIPT_DIR"
chmod +x ./server_bin/server_linux
./server_bin/server_linux &
```

---

## 4. GitHub Actions CI/CD Build Pipeline (macOS / Linux / Windows)

To compile native standalone executables without requiring local macOS hardware, a GitHub Actions workflow executes `PyInstaller` on a matrix of virtual machines.

### `.github/workflows/build_executables.yml` Specification

```yaml
name: Build Portable Executables

on:
  push:
    tags:
      - 'v*'
  workflow_dispatch:

jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        include:
          - os: windows-latest
            output_name: server_win.exe
          - os: ubuntu-latest
            output_name: server_linux
          - os: macos-latest
            output_name: server_mac

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pyinstaller pillow

      - name: Build Standalone Executable with PyInstaller
        run: |
          pyinstaller --onefile --name ${{ matrix.output_name }} server.py

      - name: Upload Build Artifacts
        uses: actions/upload-artifact@v4
        with:
          name: executable-${{ matrix.os }}
          path: dist/${{ matrix.output_name }}
```

Running this pipeline produces `server_win.exe`, `server_linux`, and `server_mac`, which are placed in `server_bin/` on the USB drive.
