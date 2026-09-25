"""Console launcher for Minecraft: Legacy Console Edition."""

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from urllib.request import urlopen
import zipfile


CONFIG_VERSION = 2
DOWNLOAD_SOURCES = {
    "archive": "https://github.com/hw2007/LCE-Verified-Archive/releases/download/Latest/LCEWindows64.zip",
    "nightly-revelations": "https://github.com/itsRevela/LCE-Revelations/releases/download/Nightly/LCE-Revelations-Client-Win64.zip",
    "nightly-mclce": "https://github.com/MCLCE/MinecraftConsoles/releases/download/nightly/LCEWindows64.zip",
}


def data_dir():
    override = os.environ.get("LEGLI_HOME")
    if override:
        return Path(override).expanduser().resolve()

    # Continue using installations made by the original launcher.
    candidates = [Path.cwd() / "LegacyLauncher"]
    if getattr(sys, "frozen", False):
        candidates.append(Path(sys.executable).resolve().parent / "LegacyLauncher")
    else:
        candidates.append(Path(__file__).resolve().parent / "LegacyLauncher")
    for candidate in candidates:
        if (candidate / "Minecraft_LCE").exists() or (candidate / "options.txt").exists():
            return candidate

    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return base / "legli"
    return Path.home() / ".local" / "share" / "legli"


def load_config(root):
    config = {"name": "Steve", "fullscreen": True, "source": "archive", "url": ""}
    path = root / "options.txt"
    if not path.exists():
        return config
    lines = path.read_text(encoding="utf-8").splitlines()
    if lines and not lines[0].isdigit():
        lines.insert(0, "0")
    if len(lines) > 1:
        config["name"] = lines[1]
    if len(lines) > 2:
        config["url"] = lines[2]
    if len(lines) > 3:
        config["fullscreen"] = lines[3] == "True"
    if len(lines) > 4:
        config["source"] = lines[4]
    return config


def save_config(root, config):
    game_dir = root / "Minecraft_LCE"
    game_dir.mkdir(parents=True, exist_ok=True)
    (root / "options.txt").write_text(
        f'{CONFIG_VERSION}\n{config["name"]}\n{config["url"]}\n'
        f'{config["fullscreen"]}\n{config["source"]}', encoding="utf-8"
    )
    (game_dir / "options.txt").write_text(
        f'fullscreen={int(config["fullscreen"])}', encoding="utf-8"
    )


def download_game(url, game_dir):
    game_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="legli-") as temp:
        temp_dir = Path(temp)
        archive = temp_dir / "game.zip"
        print("Downloading Minecraft LCE...")
        with urlopen(url, timeout=60) as response, archive.open("wb") as output:
            shutil.copyfileobj(response, output)
        print("Extracting Minecraft LCE...")
        extracted = temp_dir / "extracted"
        extracted.mkdir()
        with zipfile.ZipFile(archive) as zipped:
            for member in zipped.infolist():
                target = (extracted / member.filename).resolve()
                if not target.is_relative_to(extracted.resolve()):
                    raise ValueError("Download contains an unsafe path.")
                if member.filename.replace("\\", "/").startswith("/"):
                    raise ValueError("Download contains an unsafe path.")
            zipped.extractall(extracted)
        items = list(extracted.iterdir())
        source = items[0] if len(items) == 1 and items[0].is_dir() else extracted
        for item in source.iterdir():
            target = game_dir / item.name
            if target.is_dir():
                shutil.rmtree(target)
            elif target.exists():
                target.unlink()
            shutil.move(str(item), str(target))
    if not (game_dir / "Minecraft.Client.exe").is_file():
        raise ValueError("Download did not contain Minecraft.Client.exe.")


def launch(args):
    root = data_dir()
    game_dir = root / "Minecraft_LCE"
    config = load_config(root)
    if args.name is not None:
        if "\n" in args.name or "\r" in args.name or not args.name.strip():
            raise ValueError("Player name must be nonempty and contain no line breaks.")
        config["name"] = args.name
    if args.fullscreen is not None:
        config["fullscreen"] = args.fullscreen
    if args.source is not None:
        config["source"] = args.source
    if args.url is not None:
        config["url"] = args.url
        config["source"] = "custom"

    executable = game_dir / "Minecraft.Client.exe"
    if not executable.is_file():
        url = config["url"] if config["source"] == "custom" else DOWNLOAD_SOURCES.get(config["source"])
        if not url or not url.startswith(("https://", "http://")):
            raise ValueError("A valid HTTP(S) download URL is required.")
        download_game(url, game_dir)

    save_config(root, config)
    subprocess.Popen([str(executable), "-name", config["name"]], cwd=game_dir)
    print(f'Launched Minecraft LCE as {config["name"]}.')
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="legli", description="Minecraft: Legacy Console Edition launcher")
    commands = parser.add_subparsers(dest="command")
    commands.add_parser("help", help="Show this help message")
    launch_parser = commands.add_parser("launch", help="Install if needed, then launch the game")
    launch_parser.add_argument("--name", help="Player name (saved for future launches)")
    display = launch_parser.add_mutually_exclusive_group()
    display.add_argument("--fullscreen", action="store_const", const=True, dest="fullscreen")
    display.add_argument("--windowed", action="store_const", const=False, dest="fullscreen")
    launch_parser.set_defaults(fullscreen=None)
    launch_parser.add_argument("--source", choices=(*DOWNLOAD_SOURCES, "custom"), help="Download source if game is missing")
    launch_parser.add_argument("--url", help="Custom game ZIP URL if game is missing")
    args = parser.parse_args(argv)
    if args.command in (None, "help"):
        parser.print_help()
        return 0
    try:
        return launch(args)
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        print(f"legli: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
