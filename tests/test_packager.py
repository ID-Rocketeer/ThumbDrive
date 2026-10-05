import os
import json
import shutil
import tempfile
import unittest
import pathlib
from unittest.mock import patch

try:
    import package_thumbdrive
except ImportError:
    package_thumbdrive = None


class TestPackageThumbdrive(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(package_thumbdrive, "package_thumbdrive module must exist")
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.base_dir = pathlib.Path(self.tmp_dir.name)

        # Create mock input directories
        self.audio_dir = self.base_dir / "src_audio"
        self.audio_dir.mkdir()
        (self.audio_dir / "track1.mp3").write_bytes(b"MP3_DATA_1")
        (self.audio_dir / "track2.ogg").write_bytes(b"OGG_DATA_2")

        self.wallpaper_dir = self.base_dir / "src_wallpapers"
        self.wallpaper_dir.mkdir()
        (self.wallpaper_dir / "wp1.webp").write_bytes(b"WEBP_DATA_1")
        (self.wallpaper_dir / "wp2.webp").write_bytes(b"WEBP_DATA_2")

        self.bin_dir = self.base_dir / "src_bins"
        self.bin_dir.mkdir()
        (self.bin_dir / "server_win.exe").write_bytes(b"EXE_WIN")
        (self.bin_dir / "server_mac").write_bytes(b"BIN_MAC")
        (self.bin_dir / "server_linux").write_bytes(b"BIN_LINUX")

        self.output_dir = self.base_dir / "target_output"

    def tearDown(self):
        self.tmp_dir.cleanup()

    def test_package_thumbdrive_assembly(self):
        """
        Tests that package_thumbdrive builds the complete target folder layout with
        executables, launchers, assets, wallpapers, and current_wallpaper.json.
        """
        args = [
            "--output", str(self.output_dir),
            "--audio-dir", str(self.audio_dir),
            "--wallpaper-dir", str(self.wallpaper_dir),
            "--bin-dir", str(self.bin_dir)
        ]

        result = package_thumbdrive.main(args)
        self.assertEqual(result, 0)

        # Verify output directory structure
        self.assertTrue(self.output_dir.exists())
        self.assertTrue((self.output_dir / "assets").exists())
        self.assertTrue((self.output_dir / "assets" / "wallpapers").exists())
        self.assertTrue((self.output_dir / "server_bin").exists())

        # Verify copied launchers and readme
        self.assertTrue((self.output_dir / "Start_Windows.bat").exists())
        self.assertTrue((self.output_dir / "Start_Mac.command").exists())
        self.assertTrue((self.output_dir / "Start_Linux.sh").exists())
        self.assertTrue((self.output_dir / "README.txt").exists())

        # Verify copied executables
        self.assertTrue((self.output_dir / "server_bin" / "server_win.exe").exists())
        self.assertTrue((self.output_dir / "server_bin" / "server_mac").exists())
        self.assertTrue((self.output_dir / "server_bin" / "server_linux").exists())

        # Verify copied audio tracks in assets/
        self.assertTrue((self.output_dir / "assets" / "track1.mp3").exists())
        self.assertTrue((self.output_dir / "assets" / "track2.ogg").exists())

        # Verify copied wallpapers in assets/wallpapers/
        self.assertTrue((self.output_dir / "assets" / "wallpapers" / "wp1.webp").exists())
        self.assertTrue((self.output_dir / "assets" / "wallpapers" / "wp2.webp").exists())

        # Verify generated current_wallpaper.json in assets/
        json_file = self.output_dir / "assets" / "current_wallpaper.json"
        self.assertTrue(json_file.exists())
        data = json.loads(json_file.read_text(encoding="utf-8"))
        self.assertIn("active_wallpaper", data)
        self.assertEqual(data["active_wallpaper"], os.path.join("wallpapers", "wp1.webp"))


if __name__ == "__main__":
    unittest.main()
