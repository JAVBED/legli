# legli

legli is a Windows command-line launcher for Minecraft: Legacy Console Edition. On the first `launch`, it downloads the [verified Windows 64-bit archive](https://github.com/hw2007/LCE-Verified-Archive/releases/download/Latest/LCEWindows64.zip), extracts it, saves your options, and starts `Minecraft.Client.exe`. Later launches reuse the installed game.

## Download and run

1. Download `legli.exe` from [Releases](https://github.com/JAVBED/legli/releases).
2. Open PowerShell in the folder containing the downloaded file.
3. Run:

   ```powershell
   .\legli.exe launch
   ```

The first run needs an internet connection and enough disk space for the game. The launcher stores the game and settings in `%LOCALAPPDATA%\legli` by default. It can also reuse an older `LegacyLauncher\Minecraft_LCE` installation in the current directory or beside `legli.exe`.

## Options

```powershell
.\legli.exe help
.\legli.exe launch --name Alex --windowed
.\legli.exe launch --fullscreen
```

The player name and fullscreen choice are saved for later launches. To put the game and settings in a specific folder, set `LEGLI_HOME` before running the launcher:

```powershell
$env:LEGLI_HOME = 'D:\Games\legli'
.\legli.exe launch
```

The verified archive is the default download. You can choose another built-in source with `--source nightly-revelations` or `--source nightly-mclce`, or supply a game ZIP with `--url https://example.com/game.zip`. These options matter when the game is missing; an installed game is reused.

## Develop locally

Requires Python 3.9 or newer. From the repository root:

```powershell
python -m unittest discover -s tests -v
python legli.py launch
```

To build the Windows executable locally:

```powershell
python -m pip install "pyinstaller>=6,<7"
python -m PyInstaller --clean --noconfirm legli.spec
.\dist\legli.exe help
```

The game is downloaded at launch time and is not bundled into `legli.exe`.

## Publish a Windows release

The [release workflow](.github/workflows/release.yml) runs only when started manually from **Actions → Build Windows release → Run workflow**. It runs the tests, builds `legli.exe` on a Windows runner, checks that the executable starts, and publishes it to GitHub Releases under a unique `build-<run number>` tag. Pushes and pull requests do not start a release build.
