# Creating a Distributable Version of Glowpoint

This guide explains how to create a standalone executable version of Glowpoint that can run on computers without Python installed.

## Overview

Glowpoint uses PyInstaller to bundle the Python interpreter and all dependencies into a single executable file. This makes it easy to distribute the application to users who don't have Python installed.

## Prerequisites

You need Python installed on YOUR development machine to build the distribution. Your coworkers who receive the built executable will NOT need Python.

## Building the Distribution

### Windows

1. Open a command prompt in the Glowpoint folder
2. Run the build script:
   ```
   build_dist.bat
   ```
3. Wait for the build to complete (this may take a few minutes)
4. The distributable version will be created in the `Glowpoint_Portable` folder

### What Gets Created

The build process creates:
- `Glowpoint_Portable/Glowpoint.exe` - The standalone executable
- `Glowpoint_Portable/README.txt` - User instructions
- `Glowpoint_Portable/LICENSE` - License file

## Distributing to Others

Simply copy the entire `Glowpoint_Portable` folder to another computer. Users can:
1. Double-click `Glowpoint.exe` to run the application
2. No installation required
3. No Python required
4. All dependencies are bundled

## Distribution Size

The executable will be approximately 30-50 MB due to the bundled Python runtime and PyQt5 libraries. This is normal for Python applications distributed with PyInstaller.

## Troubleshooting

### Build Fails

- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Try cleaning build artifacts: Delete `build/` and `dist/` folders, then rebuild
- Check Python version: Python 3.7+ is required

### Executable Doesn't Run

- Windows may show a security warning for unsigned executables - click "More info" then "Run anyway"
- Antivirus software may flag the executable (false positive) - add an exception if needed
- Make sure all files in `Glowpoint_Portable` are kept together

### Slow Startup

The first startup may be slower (5-10 seconds) as PyInstaller extracts temporary files. Subsequent startups will be faster.

## Alternative: Manual PyInstaller Command

If you prefer to run PyInstaller manually:

```bash
pyinstaller glowpoint.spec --clean
```

The executable will be created in `dist/Glowpoint.exe`.

## For Developers

The build configuration is in `glowpoint.spec`. Key settings:
- `console=False` - No console window appears
- `onefile` mode (in EXE section) - Single executable file
- Hidden imports for PyQt5 and pynput modules
- UPX compression enabled for smaller file size
