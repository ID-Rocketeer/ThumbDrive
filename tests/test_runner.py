import os
import sys
import unittest
from unittest.mock import MagicMock, patch
import socket
import tempfile
import pathlib
import time

# Target modules to test (will fail import or test until implemented)
try:
    import thumbdrive_runner
except ImportError:
    thumbdrive_runner = None


class TestPortSelection(unittest.TestCase):
    def test_find_available_port_preferred_free(self):
        """
        Tests that find_available_port returns the preferred port when free.
        """
        self.assertIsNotNone(thumbdrive_runner, "thumbdrive_runner module must exist")
        # Pick a free port
        temp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        temp_sock.bind(("127.0.0.1", 0))
        free_port = temp_sock.getsockname()[1]
        temp_sock.close()

        port = thumbdrive_runner.find_available_port("127.0.0.1", preferred_port=free_port)
        self.assertEqual(port, free_port)

    def test_find_available_port_preferred_occupied(self):
        """
        Tests that find_available_port falls back to a different free port when preferred port is occupied.
        """
        self.assertIsNotNone(thumbdrive_runner, "thumbdrive_runner module must exist")
        # Occupy a port
        occ_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        occ_sock.bind(("127.0.0.1", 0))
        occupied_port = occ_sock.getsockname()[1]

        try:
            port = thumbdrive_runner.find_available_port("127.0.0.1", preferred_port=occupied_port)
            self.assertNotEqual(port, occupied_port)
            self.assertGreater(port, 0)
        finally:
            occ_sock.close()


class TestSocketPolling(unittest.TestCase):
    def test_wait_for_server_and_open_browser_success(self):
        """
        Tests that wait_for_server_and_open_browser successfully detects an open socket
        and calls webbrowser.open.
        """
        self.assertIsNotNone(thumbdrive_runner, "thumbdrive_runner module must exist")
        
        # Create a mock TCP server to bind a local port
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.bind(("127.0.0.1", 0))
        server_sock.listen(1)
        port = server_sock.getsockname()[1]

        try:
            with patch("webbrowser.open") as mock_open:
                success = thumbdrive_runner.wait_for_server_and_open_browser("127.0.0.1", port, timeout=2.0)
                self.assertTrue(success)
                mock_open.assert_called_once_with(f"http://127.0.0.1:{port}")
        finally:
            server_sock.close()

    def test_wait_for_server_and_open_browser_timeout(self):
        """
        Tests that wait_for_server_and_open_browser returns False on timeout if no server responds.
        """
        self.assertIsNotNone(thumbdrive_runner, "thumbdrive_runner module must exist")
        
        # Pick a port that is not listening
        unused_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        unused_sock.bind(("127.0.0.1", 0))
        port = unused_sock.getsockname()[1]
        unused_sock.close()

        with patch("webbrowser.open") as mock_open:
            success = thumbdrive_runner.wait_for_server_and_open_browser("127.0.0.1", port, timeout=0.3)
            self.assertFalse(success)
            mock_open.assert_not_called()


class TestRunnerOrchestration(unittest.TestCase):
    @patch("thumbdrive_runner.PaperHanger")
    @patch("thumbdrive_runner.create_server_instance")
    @patch("thumbdrive_runner.threading.Thread")
    def test_main_orchestration(self, mock_thread_cls, mock_create_server, mock_paperhanger_cls):
        """
        Tests that main() initializes PaperHanger on assets/, spawns background threads,
        and starts the audio server on assets/.
        """
        self.assertIsNotNone(thumbdrive_runner, "thumbdrive_runner module must exist")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = pathlib.Path(tmpdir)
            assets_dir = tmp_path / "assets"
            assets_dir.mkdir(parents=True, exist_ok=True)

            mock_thread_instance = MagicMock()
            mock_thread_cls.return_value = mock_thread_instance

            mock_server_inst = MagicMock()
            mock_create_server.return_value = (mock_server_inst, 8000)

            with patch("pathlib.Path.cwd", return_value=tmp_path):
                thumbdrive_runner.main(["--port", "8000"])

            # Verify PaperHanger thread and browser thread creation
            self.assertGreaterEqual(mock_thread_cls.call_count, 2)
            # Verify create_server_instance called with assets directory and assigned port
            mock_create_server.assert_called_once()
            _, kwargs = mock_create_server.call_args
            self.assertGreater(kwargs.get("port"), 0)
            self.assertEqual(pathlib.Path(kwargs.get("audio_dir")).resolve(), assets_dir.resolve())


if __name__ == "__main__":
    unittest.main()
