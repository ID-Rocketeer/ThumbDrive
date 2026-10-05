#!/usr/bin/env python3
"""
Package ThumbDrive: Assembles a complete, user-facing USB drive file structure.
Enforces strict verification on all required inputs (audio files, .webp wallpapers,
title.json config files, and cross-platform executables).
Fails immediately if any required component is missing.
"""

import argparse
import json
import os
import pathlib
import shutil
import sys

SUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".ogg", ".wav", ".flac", ".m4a", ".aac", ".opus", ".wma"}
REQUIRED_BINARIES = ["server_win.exe", "server_mac", "server_linux"]

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
    parser = argparse.ArgumentParser(
        description="Assemble ThumbDrive USB layout into target directory with strict input validation."
    )
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Target output directory (e.g. E:\\ or ./build/usb_image)"
    )
    parser.add_argument(
        "-a", "--audio-dir",
        required=True,
        help="Source directory containing protected audio files"
    )
    parser.add_argument(
        "-w", "--wallpaper-dir",
        required=True,
        help="Source directory containing protected .webp wallpaper files"
    )
    parser.add_argument(
        "-b", "--bin-dir",
        required=True,
        help="Source directory containing the 3 pre-compiled executables (server_win.exe, server_mac, server_linux)"
    )
    parser.add_argument(
        "-t", "--title-file",
        help="Optional source path to title.json file (e.g. /path/to/title.json)"
    )
    return parser.parse_args(args)


def validate_inputs(audio_dir_path: pathlib.Path, wallpaper_dir_path: pathlib.Path, bin_dir_path: pathlib.Path, title_file_path: pathlib.Path | None = None):
    """
    Strictly verifies that source directories and optional title file exist and contain valid assets.
    Exits with error if validation fails.
    """
    # 1. Validate Executables Directory
    if not bin_dir_path.exists() or not bin_dir_path.is_dir():
        sys.stderr.write(f"ERROR: Executables directory '{bin_dir_path}' does not exist or is not a directory.\n")
        sys.exit(1)

    missing_bins = [exe for exe in REQUIRED_BINARIES if not (bin_dir_path / exe).is_file()]
    if missing_bins:
        sys.stderr.write(
            f"ERROR: Missing required executable(s) in '{bin_dir_path}': {', '.join(missing_bins)}\n"
            f"All three compiled binaries ({', '.join(REQUIRED_BINARIES)}) are required to assemble the image.\n"
        )
        sys.exit(1)

    # 2. Validate Audio Directory
    if not audio_dir_path.exists() or not audio_dir_path.is_dir():
        sys.stderr.write(f"ERROR: Audio directory '{audio_dir_path}' does not exist or is not a directory.\n")
        sys.exit(1)

    audio_files = [
        f for f in audio_dir_path.iterdir()
        if f.is_file() and not f.name.startswith(".") and f.suffix.lower() in SUPPORTED_AUDIO_EXTENSIONS
    ]
    if not audio_files:
        sys.stderr.write(
            f"ERROR: No supported audio files ({', '.join(sorted(SUPPORTED_AUDIO_EXTENSIONS))}) found in '{audio_dir_path}'.\n"
        )
        sys.exit(1)

    # 3. Validate Wallpaper Directory
    if not wallpaper_dir_path.exists() or not wallpaper_dir_path.is_dir():
        sys.stderr.write(f"ERROR: Wallpaper directory '{wallpaper_dir_path}' does not exist or is not a directory.\n")
        sys.exit(1)

    wallpaper_files = [
        f for f in wallpaper_dir_path.iterdir()
        if f.is_file() and not f.name.startswith(".") and f.suffix.lower() == ".webp"
    ]
    if not wallpaper_files:
        sys.stderr.write(f"ERROR: No valid .webp wallpaper files found in '{wallpaper_dir_path}'.\n")
        sys.exit(1)

    # 4. Validate Title File if specified
    if title_file_path is not None:
        if not title_file_path.exists() or not title_file_path.is_file():
            sys.stderr.write(f"ERROR: Title file '{title_file_path}' does not exist or is not a valid file.\n")
            sys.exit(1)

    return audio_files, wallpaper_files


def main(args=None):
    parsed = parse_args(args)

    output_dir = pathlib.Path(parsed.output).resolve()
    audio_dir_path = pathlib.Path(parsed.audio_dir).resolve()
    wallpaper_dir_path = pathlib.Path(parsed.wallpaper_dir).resolve()
    bin_dir_path = pathlib.Path(parsed.bin_dir).resolve()
    title_file_path = pathlib.Path(parsed.title_file).resolve() if parsed.title_file else None

    # Perform strict validation upfront
    audio_files, wallpaper_files = validate_inputs(audio_dir_path, wallpaper_dir_path, bin_dir_path, title_file_path)

    # Prepare target directory paths
    target_assets_dir = output_dir / "assets"
    wallpapers_dir = target_assets_dir / "wallpapers"
    target_bin_dir = output_dir / "server_bin"

    # 1. Create target output directories
    target_assets_dir.mkdir(parents=True, exist_ok=True)
    wallpapers_dir.mkdir(parents=True, exist_ok=True)
    target_bin_dir.mkdir(parents=True, exist_ok=True)

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

    # 3. Copy validated executables to server_bin/
    for exe_name in REQUIRED_BINARIES:
        src_exe = bin_dir_path / exe_name
        shutil.copy2(src_exe, target_bin_dir / exe_name)
        if not exe_name.endswith(".exe"):
            try:
                (target_bin_dir / exe_name).chmod(0o755)
            except OSError:
                pass

    # 4. Copy validated audio files to assets/
    for item in audio_files:
        shutil.copy2(item, target_assets_dir / item.name)

    # 5. Copy title.json if specified via --title-file
    if title_file_path:
        shutil.copy2(title_file_path, target_assets_dir / "title.json")

    # 6. Copy validated .webp wallpapers to assets/wallpapers/
    for item in wallpaper_files:
        shutil.copy2(item, wallpapers_dir / item.name)

    # 7. Initialize current_wallpaper.json with first naturally sorted .webp file if not already present
    sorted_wp_names = sorted([f.name for f in wallpaper_files])
    first_wp = os.path.join("wallpapers", sorted_wp_names[0])
    json_data = {
        "active_wallpaper": first_wp,
        "updated_at": 1791145900
    }
    json_file = target_assets_dir / "current_wallpaper.json"
    if not json_file.exists():
        json_file.write_text(json.dumps(json_data, indent=2) + "\n", encoding="utf-8")

    print(f"ThumbDrive USB image successfully generated at: {output_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
