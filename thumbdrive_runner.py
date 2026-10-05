#!/usr/bin/env python3
"""
ThumbDrive Runner: Entry-point application for the self-contained portable USB Audio Web Server.
Orchestrates PaperHanger (background wallpaper swapper) and Halloween (audio web server),
auto-launches the web browser once the socket is live, and automatically shuts down
when all browser windows/tabs are closed.
"""

import argparse
import os
import pathlib
import socket
import sys
import threading
import time
import traceback
import webbrowser

# Add adjacent project directories to sys.path for local un-frozen execution if needed
CURRENT_DIR = pathlib.Path(__file__).parent.resolve()
PARENT_DIR = CURRENT_DIR.parent

for extra_path in [PARENT_DIR / "PaperHanger", PARENT_DIR / "Halloween"]:
    if extra_path.exists() and str(extra_path) not in sys.path:
        sys.path.insert(0, str(extra_path))

try:
    from paperhanger import PaperHanger
except ImportError:
    PaperHanger = None

try:
    from audio_server.server import create_server_instance, AudioServerRequestHandler
except ImportError:
    create_server_instance = None
    AudioServerRequestHandler = None


class SocketConnectionTracker:
    def __init__(self):
        self.active_sockets = 0
        self.lock = threading.Lock()
        self.has_connected = False
        self.idle_since = None

    def on_socket_connect(self):
        with self.lock:
            self.active_sockets += 1
            self.has_connected = True
            self.idle_since = None

    def on_socket_disconnect(self):
        with self.lock:
            self.active_sockets = max(0, self.active_sockets - 1)
            if self.active_sockets == 0 and self.has_connected:
                self.idle_since = time.time()

    def check_and_shutdown_if_idle(self, server, idle_grace_seconds: float = 8.0) -> bool:
        with self.lock:
            if self.has_connected and self.active_sockets == 0:
                if self.idle_since is not None and (time.time() - self.idle_since) >= idle_grace_seconds:
                    sys.stdout.write("\n[ThumbDrive] All browser windows closed. Auto-shutting down server...\n")
                    try:
                        server.shutdown()
                    except Exception:
                        pass
                    return True
        return False


global_tracker = SocketConnectionTracker()


def install_socket_hooks():
    if AudioServerRequestHandler is None:
        return

    # Set HTTP socket timeout so idle Keep-Alive connections close fast when tab is closed
    AudioServerRequestHandler.timeout = 1.5

    if not hasattr(AudioServerRequestHandler, "_thumbdrive_orig_setup"):
        original_setup = AudioServerRequestHandler.setup
        original_finish = AudioServerRequestHandler.finish

        def patched_setup(self):
            original_setup(self)
            global_tracker.on_socket_connect()

        def patched_finish(self):
            try:
                original_finish(self)
            finally:
                global_tracker.on_socket_disconnect()

        AudioServerRequestHandler._thumbdrive_orig_setup = original_setup
        AudioServerRequestHandler.setup = patched_setup
        AudioServerRequestHandler.finish = patched_finish


def wait_for_server_and_open_browser(host: str, port: int, timeout: float = 10.0) -> bool:
    """
    Polls host:port until the TCP socket is bound and listening,
    then opens the default web browser to the URL.
    Returns True on success, False if timed out.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            with socket.create_connection((host, port), timeout=0.2):
                webbrowser.open(f"http://{host}:{port}")
                return True
        except (OSError, ConnectionRefusedError):
            time.sleep(0.1)
    return False


def run_paperhanger_service(target_dir: pathlib.Path):
    """
    Runs PaperHanger wallpaper rotation service in a background daemon thread.
    """
    if PaperHanger is None:
        sys.stderr.write("Warning: PaperHanger module not found. Wallpaper rotation disabled.\n")
        return

    wallpapers_dir = target_dir / "wallpapers"
    if not wallpapers_dir.exists() or not wallpapers_dir.is_dir():
        sys.stderr.write(f"Warning: Wallpapers directory '{wallpapers_dir}' missing. PaperHanger idle.\n")
        return

    try:
        service = PaperHanger(str(target_dir))
        service.run()
    except SystemExit as e:
        sys.stderr.write(f"PaperHanger notice: exited with status {e.code}\n")
    except Exception as e:
        sys.stderr.write(f"PaperHanger warning: {e}\n")


def parse_args(args=None):
    parser = argparse.ArgumentParser(description="ThumbDrive Audio Web Server Launcher")
    parser.add_argument(
        "-p", "--port",
        type=int,
        default=8000,
        help="Port to run HTTP server on (default: 8000)"
    )
    parser.add_argument(
        "-H", "--host",
        default="127.0.0.1",
        help="Host address to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "-d", "--dir",
        dest="target_dir",
        default=None,
        help="Path to assets directory containing audio and wallpapers/ (default: auto-detect assets/)"
    )
    return parser.parse_args(args)


def run_server(target_dir: pathlib.Path, host: str = "127.0.0.1", port: int = 8000):
    if create_server_instance is None:
        raise ImportError("ERROR: Halloween audio_server module not found.")

    install_socket_hooks()

    server, assigned_port = create_server_instance(
        audio_dir=str(target_dir),
        host=host,
        port=port
    )
    print(f"[ThumbDrive] Audio Server listening on http://{host}:{assigned_port}")
    print(f"[ThumbDrive] Hosting audio files from: {target_dir}")
    print("Press Ctrl+C or close browser to stop.")

    # Start auto-shutdown monitor loop
    def monitor_loop():
        while True:
            time.sleep(0.5)
            if global_tracker.check_and_shutdown_if_idle(server, idle_grace_seconds=3.0):
                break

    threading.Thread(target=monitor_loop, daemon=True, name="AutoShutdownMonitor").start()

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping audio server...")
        server.shutdown()
        server.server_close()


def find_available_port(host: str = "127.0.0.1", preferred_port: int = 8000) -> int:
    """
    Attempts to bind preferred_port. If occupied, lets the OS assign an available open port.
    Returns the open port integer.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, preferred_port))
            return preferred_port
        except OSError:
            s.bind((host, 0))
            return s.getsockname()[1]


def main(args=None):
    parsed = parse_args(args)
    
    # Resolve assets directory path
    if parsed.target_dir:
        assets_path = pathlib.Path(parsed.target_dir).resolve()
    else:
        root_dir = pathlib.Path.cwd()
        if (root_dir / "assets").exists():
            assets_path = (root_dir / "assets").resolve()
        else:
            assets_path = root_dir.resolve()

    if not assets_path.exists():
        sys.stderr.write(f"ERROR: Assets directory '{assets_path}' does not exist.\n")
        sys.exit(1)

    # Determine dynamic open port (preferred 8000, fallback to OS assigned open port)
    active_port = find_available_port(parsed.host, preferred_port=parsed.port)
    if active_port != parsed.port:
        sys.stdout.write(f"[ThumbDrive] Preferred port {parsed.port} in use. Dynamically assigned open port {active_port}.\n")

    # 1. Start PaperHanger background wallpaper rotation service in a daemon thread
    swapper_thread = threading.Thread(
        target=run_paperhanger_service,
        args=(assets_path,),
        daemon=True,
        name="PaperHangerThread"
    )
    swapper_thread.start()

    # 2. Start socket polling browser auto-launcher in a daemon thread
    browser_thread = threading.Thread(
        target=wait_for_server_and_open_browser,
        args=(parsed.host, active_port),
        daemon=True,
        name="BrowserLauncherThread"
    )
    browser_thread.start()

    # 3. Start Halloween Audio Server in the main thread
    run_server(target_dir=assets_path, host=parsed.host, port=active_port)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        sys.stderr.write("\n===================================================\n")
        sys.stderr.write("FATAL ERROR IN THUMBDRIVE RUNNER:\n")
        sys.stderr.write(f"{exc}\n")
        traceback.print_exc()
        sys.stderr.write("===================================================\n")
        try:
            input("Press Enter to exit...")
        except Exception:
            pass
        sys.exit(1)
