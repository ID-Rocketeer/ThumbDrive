# ThumbDrive Audio Server

A portable, cross-platform web server for serving audio tracks and rotating wallpaper themes directly from a USB thumb drive across **Windows**, **macOS**, and **Linux**.

---

## 📁 USB Drive Layout

```text
USB_DRIVE/
├── README.md               # User documentation
├── ARCHITECTURE.md         # Technical specifications & CI build pipeline
├── Start_Windows.bat       # Double-click launcher for Windows
├── Start_Mac.command       # Double-click launcher for macOS
├── Start_Linux.sh          # Double-click launcher for Linux
├── current_wallpaper.json  # PaperHanger active wallpaper pointer
├── audio/                  # Audio track files (.ogg, .mp3, .flac, .wav)
├── wallpapers/             # Wallpaper image gallery (.webp, .png, .jpg)
└── server_bin/             # Pre-compiled standalone executables
    ├── server_win.exe      # Windows executable (built via PyInstaller)
    ├── server_mac          # macOS executable (built via GitHub Actions)
    └── server_linux        # Linux executable (built via PyInstaller)
```

---

## 🚀 Quick Start

1. Plug the USB drive into any Windows, macOS, or Linux computer.
2. Double-click the launcher corresponding to your operating system:
   - **Windows**: `Start_Windows.bat`
   - **macOS**: `Start_Mac.command`
   - **Linux**: `Start_Linux.sh`
3. The server starts silently on `localhost` and automatically opens your default web browser to the audio player interface.

---

## 🎨 Wallpaper Swapping (`PaperHanger` Integration)

On exFAT and FAT32 USB filesystems, symbolic links are not supported across operating systems. To support `PaperHanger` wallpaper swapping across Windows, Mac, and Linux:

* `PaperHanger` updates `current_wallpaper.json` to point to the desired image file inside `wallpapers/`.
* The server reads `current_wallpaper.json` on `/wallpaper` HTTP requests and serves the active image.
