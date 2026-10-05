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

        self.title_file = self.base_dir / "title.json"
        self.title_file.write_text('{"title": "Custom Spooky Server"}', encoding="utf-8")

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

    def test_package_thumbdrive_wallpaper_filtering(self):
        """
        Tests that package_thumbdrive copies ONLY .webp wallpaper files,
        ignoring .png, .zip, .pdf, or other non-.webp files in wallpaper_dir.
        """
        # Add non-.webp files to wallpaper_dir
        (self.wallpaper_dir / "uncompressed.png").write_bytes(b"PNG_DATA")
        (self.wallpaper_dir / "archive.zip").write_bytes(b"ZIP_DATA")
        (self.wallpaper_dir / "access.pdf").write_bytes(b"PDF_DATA")

        args = [
            "--output", str(self.output_dir),
            "--audio-dir", str(self.audio_dir),
            "--wallpaper-dir", str(self.wallpaper_dir),
            "--bin-dir", str(self.bin_dir)
        ]

        result = package_thumbdrive.main(args)
        self.assertEqual(result, 0)

        target_wp_dir = self.output_dir / "assets" / "wallpapers"
        copied_files = sorted([f.name for f in target_wp_dir.iterdir() if f.is_file()])

        # Should only contain .webp files
        self.assertEqual(copied_files, ["wp1.webp", "wp2.webp"])
        self.assertNotIn("uncompressed.png", copied_files)
        self.assertNotIn("archive.zip", copied_files)
        self.assertNotIn("access.pdf", copied_files)

    def test_package_thumbdrive_missing_binary_fails(self):
        """
        Tests that package_thumbdrive fails if any of the 3 required binaries
        (server_win.exe, server_mac, server_linux) is missing in bin_dir.
        """
        # Remove server_win.exe
        (self.bin_dir / "server_win.exe").unlink()

        args = [
            "--output", str(self.output_dir),
            "--audio-dir", str(self.audio_dir),
            "--wallpaper-dir", str(self.wallpaper_dir),
            "--bin-dir", str(self.bin_dir)
        ]

        with self.assertRaises((SystemExit, ValueError)):
            package_thumbdrive.main(args)

    def test_package_thumbdrive_empty_audio_dir_fails(self):
        """
        Tests that package_thumbdrive fails if audio_dir contains no valid audio files.
        """
        empty_audio = self.base_dir / "empty_audio"
        empty_audio.mkdir()

        args = [
            "--output", str(self.output_dir),
            "--audio-dir", str(empty_audio),
            "--wallpaper-dir", str(self.wallpaper_dir),
            "--bin-dir", str(self.bin_dir)
        ]

        with self.assertRaises((SystemExit, ValueError)):
            package_thumbdrive.main(args)

    def test_package_thumbdrive_empty_wallpaper_dir_fails(self):
        """
        Tests that package_thumbdrive fails if wallpaper_dir contains no .webp files.
        """
        empty_wp = self.base_dir / "empty_wp"
        empty_wp.mkdir()

        args = [
            "--output", str(self.output_dir),
            "--audio-dir", str(self.audio_dir),
            "--wallpaper-dir", str(empty_wp),
            "--bin-dir", str(self.bin_dir)
        ]

        with self.assertRaises((SystemExit, ValueError)):
            package_thumbdrive.main(args)

    def test_package_thumbdrive_title_file_option(self):
        """
        Tests that package_thumbdrive copies title.json to target assets/title.json when --title-file is passed.
        """
        args = [
            "--output", str(self.output_dir),
            "--audio-dir", str(self.audio_dir),
            "--wallpaper-dir", str(self.wallpaper_dir),
            "--bin-dir", str(self.bin_dir),
            "--title-file", str(self.title_file)
        ]

        result = package_thumbdrive.main(args)
        self.assertEqual(result, 0)

        target_title = self.output_dir / "assets" / "title.json"
        self.assertTrue(target_title.exists())
        self.assertEqual(target_title.read_text(encoding="utf-8"), '{"title": "Custom Spooky Server"}')

    def test_package_thumbdrive_invalid_title_file_fails(self):
        """
        Tests that package_thumbdrive fails if --title-file points to a non-existent file.
        """
        non_existent_title = self.base_dir / "non_existent_title.json"

        args = [
            "--output", str(self.output_dir),
            "--audio-dir", str(self.audio_dir),
            "--wallpaper-dir", str(self.wallpaper_dir),
            "--bin-dir", str(self.bin_dir),
            "--title-file", str(non_existent_title)
        ]

        with self.assertRaises((SystemExit, ValueError)):
            package_thumbdrive.main(args)


if __name__ == "__main__":
    unittest.main()
