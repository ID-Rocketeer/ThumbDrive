#!/usr/bin/env python3
"""
Package ThumbDrive: Assembles a complete, user-facing USB drive file structure
containing launchers, standalone server executables, and media assets.
"""

import argparse
import json
import os
import pathlib
import shutil
import sys


DEFAULT_WIN_BAT = """@echo off
title ThumbDrive Audio Player
cd /d "%~dp0"
start "" "server_bin\\server_win.exe"
"""

DEFAULT_MAC_COMMAND = """#!/bin/bash
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"
chmod +x ./server_bin/server_mac
./server_bin/server_mac &
"""

DEFAULT_LINUX_SH = """#!/bin/bash
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"
cd "$SCRIPT_DIR"
chmod +x ./server_bin/server_linux
./server_bin/server_linux &
"""

DEFAULT_README_TXT = """===================================================================
                  ThumbDrive Portable Audio Server
===================================================================

Quick Start Instructions:
-------------------------
1. Double-click the launcher script for your operating system:
   - Windows: Double-click 'Start_Windows.bat'
   - macOS:   Double-click 'Start_Mac.command'
   - Linux:   Run 'Start_Linux.sh'

2. The audio web player will automatically start and open in your
   default web browser.

3. Enjoy your music and rotating wallpaper themes!
===================================================================
"""


def parse_args(args=None):
    parser = argparse.ArgumentParser(description="Assemble ThumbDrive USB layout into target directory")
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Target output directory (e.g. E:\\ or ./build/usb_image)"
    )
    parser.add_argument(
        "-a", "--audio-dir",
        help="Source directory containing protected audio files"
    )
    parser.add_argument(
        "-w", "--wallpaper-dir",
        help="Source directory containing protected .webp wallpaper files"
    )
    parser.add_argument(
        "-b", "--bin-dir",
        help="Source directory containing pre-compiled executables (server_win.exe, server_mac, server_linux)"
    )
    return parser.parse_args(args)


def main(args=None):
    parsed = parse_args(args)

    output_dir = pathlib.Path(parsed.output).resolve()
    assets_dir = output_dir / "assets"
    wallpapers_dir = assets_dir / "wallpapers"
    bin_dir = output_dir / "server_bin"

    # 1. Create target output directories
    assets_dir.mkdir(parents=True, exist_ok=True)
    wallpapers_dir.mkdir(parents=True, exist_ok=True)
    bin_dir.mkdir(parents=True, exist_ok=True)

    # 2. Write root launcher scripts and README.txt
    (output_dir / "Start_Windows.bat").write_text(DEFAULT_WIN_BAT, encoding="utf-8")
    
    mac_script = output_dir / "Start_Mac.command"
    mac_script.write_text(DEFAULT_MAC_COMMAND, encoding="utf-8")
    try:
        mac_script.chmod(0o755)
    except OSError:
        pass

    linux_script = output_dir / "Start_Linux.sh"
    linux_script.write_text(DEFAULT_LINUX_SH, encoding="utf-8")
    try:
        linux_script.chmod(0o755)
    except OSError:
        pass

    (output_dir / "README.txt").write_text(DEFAULT_README_TXT, encoding="utf-8")

    # 3. Copy compiled executables if bin_dir provided
    if parsed.bin_dir:
        src_bin = pathlib.Path(parsed.bin_dir).resolve()
        if src_bin.exists() and src_bin.is_dir():
            for exe_name in ["server_win.exe", "server_mac", "server_linux"]:
                src_exe = src_bin / exe_name
                if src_exe.exists():
                    shutil.copy2(src_exe, bin_dir / exe_name)
                    if not exe_name.endswith(".exe"):
                        try:
                            (bin_dir / exe_name).chmod(0o755)
                        except OSError:
                            pass

    # 4. Copy audio files if audio_dir provided
    if parsed.audio_dir:
        src_audio = pathlib.Path(parsed.audio_dir).resolve()
        if src_audio.exists() and src_audio.is_dir():
            for item in src_audio.iterdir():
                if item.is_file() and not item.name.startswith("."):
                    shutil.copy2(item, assets_dir / item.name)

    # 5. Copy wallpaper files if wallpaper_dir provided
    if parsed.wallpaper_dir:
        src_wallpapers = pathlib.Path(parsed.wallpaper_dir).resolve()
        if src_wallpapers.exists() and src_wallpapers.is_dir():
            for item in src_wallpapers.iterdir():
                if item.is_file() and not item.name.startswith("."):
                    shutil.copy2(item, wallpapers_dir / item.name)

    # 6. Initialize current_wallpaper.json if wallpapers exist
    wallpaper_files = sorted([f.name for f in wallpapers_dir.iterdir() if f.is_file() and f.suffix.lower() == ".webp"])
    if wallpaper_files:
        first_wp = os.path.join("wallpapers", wallpaper_files[0])
        json_data = {
            "active_wallpaper": first_wp,
            "updated_at": 1791145900
        }
        json_file = assets_dir / "current_wallpaper.json"
        json_file.write_text(json.dumps(json_data, indent=2) + "\n", encoding="utf-8")

    print(f"ThumbDrive USB image successfully generated at: {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
