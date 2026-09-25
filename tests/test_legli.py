import contextlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import zipfile

import legli


class LegliTests(unittest.TestCase):
    def test_help_lists_commands(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(legli.main(["help"]), 0)
        self.assertIn("launch", output.getvalue())

    def test_launch_reuses_legacy_install_and_saves_options(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "LegacyLauncher"
            game_dir = root / "Minecraft_LCE"
            game_dir.mkdir(parents=True)
            executable = game_dir / "Minecraft.Client.exe"
            executable.touch()
            (root / "options.txt").write_text("2\nSteve\n\nTrue\narchive", encoding="utf-8")

            with patch.object(legli, "data_dir", return_value=root), patch.object(legli.subprocess, "Popen") as popen:
                self.assertEqual(legli.main(["launch", "--name", "Alex", "--windowed"]), 0)

            popen.assert_called_once_with([str(executable), "-name", "Alex"], cwd=game_dir)
            self.assertIn("\nAlex\n", (root / "options.txt").read_text(encoding="utf-8"))
            self.assertEqual((game_dir / "options.txt").read_text(encoding="utf-8"), "fullscreen=0")

    def test_first_launch_downloads_then_starts_game(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "legli"

            def fake_download(url, game_dir):
                self.assertEqual(url, "https://github.com/hw2007/LCE-Verified-Archive/releases/download/Latest/LCEWindows64.zip")
                game_dir.mkdir(parents=True)
                (game_dir / "Minecraft.Client.exe").touch()

            with patch.object(legli, "data_dir", return_value=root), patch.object(legli, "download_game", side_effect=fake_download), patch.object(legli.subprocess, "Popen") as popen:
                self.assertEqual(legli.main(["launch"]), 0)

            popen.assert_called_once()
            self.assertTrue((root / "options.txt").exists())

    def test_download_extracts_wrapped_game_archive(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            archive = root / "game.zip"
            with zipfile.ZipFile(archive, "w") as zipped:
                zipped.writestr("release/Minecraft.Client.exe", b"game")
                zipped.writestr("release/assets/example.txt", b"asset")

            game_dir = root / "Minecraft_LCE"
            legli.download_game(archive.as_uri(), game_dir)

            self.assertEqual((game_dir / "Minecraft.Client.exe").read_bytes(), b"game")
            self.assertEqual((game_dir / "assets" / "example.txt").read_bytes(), b"asset")


if __name__ == "__main__":
    unittest.main()
