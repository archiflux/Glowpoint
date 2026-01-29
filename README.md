# Glowpoint

A lightweight cursor highlighter and screen drawing tool perfect for presentations, screen sharing, and tutorials. Highlight your cursor with an attractive spotlight effect and draw annotations on your screen in real-time!

## Features

### Spotlight Mode
- **Cursor Highlighting**: Draw attention to your cursor with a beautiful glowing spotlight effect
- **Customizable Appearance**: Adjust radius, ring size, color, and opacity
- **Live Preview**: See changes in real-time as you adjust settings

### Drawing Tools
- **Freehand Drawing**: Smooth, anti-aliased freehand drawing with glow effect
- **Straight Lines**: Click and drag to draw perfect straight lines
- **Rectangles**: Draw rectangles with sharp corners
- **Arrows**: Draw arrows with proportional arrowheads
- **Circles**: Draw perfect circles from center to edge
- **Multiple Colors**: Blue, red, yellow, and green drawing colors
- **Adjustable Thickness**: 1-20px line width, adjustable with mouse wheel
- **Feathered Glow Effect**: All drawings have a subtle glow for better visibility

### Advanced Features
- **Undo/Redo**: Ctrl+Z to undo, Ctrl+Shift+Z to redo
- **Shift+Click Lines**: In freehand mode, hold Shift and click to chain straight lines
- **Floating Toolbar**: Visual toolbar appears during drawing mode for quick tool selection
- **Multi-Monitor Support**: Works seamlessly across all your displays
- **Global Keyboard Shortcuts**: Control everything with customizable keyboard shortcuts
- **Always-on-Top Annotations**: Drawings stay visible over all windows
- **System Tray Integration**: Quick access to all features from the system tray
- **Lightweight & Efficient**: Minimal resource usage, no admin rights required

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

### Quick Start

1. **Clone or download this repository**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

   Or install manually:
   ```bash
   pip install PyQt5 pynput
   ```

3. **Run the application**:
   ```bash
   python glowpoint.py
   ```

   Or make it executable (Linux/Mac):
   ```bash
   chmod +x glowpoint.py
   ./glowpoint.py
   ```

## Usage

### Default Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| Toggle Spotlight | Ctrl+Shift+S |
| Draw Blue | Ctrl+Shift+B |
| Draw Red | Ctrl+Shift+R |
| Draw Yellow | Ctrl+Shift+Y |
| Draw Green | Ctrl+Shift+G |
| Clear All Drawings | Ctrl+Shift+C |
| Quit Application | Ctrl+Shift+Q |

**Tip**: Hover over the system tray icon to see all current shortcuts!

### Drawing Mode

1. Press a drawing shortcut (e.g., **Ctrl+Shift+B** for blue)
2. A floating toolbar appears with tool buttons
3. Use the following controls:

| Control | Action |
|---------|--------|
| Click and drag | Draw with current tool |
| Mouse wheel | Adjust line thickness (1-20px) |
| 1 | Freehand tool |
| 2 | Line tool |
| 3 | Rectangle tool |
| 4 | Arrow tool |
| 5 | Circle tool |
| Ctrl+Z | Undo last drawing |
| Ctrl+Shift+Z | Redo |
| ESC | Exit drawing mode |
| Same color hotkey | Exit drawing mode |

### Drawing Tools

- **Freehand (1)**: Click and drag to draw smooth curves. Hold Shift+Click to draw connected straight lines.
- **Line (2)**: Click and drag to draw straight lines between two points.
- **Rectangle (3)**: Click and drag from one corner to the opposite corner.
- **Arrow (4)**: Click and drag from tail to head. Arrowhead size scales with line thickness.
- **Circle (5)**: Click at center, drag to define radius.

### Pro Tips

- **Chain straight lines**: In freehand mode, Shift+Click multiple times to create connected line segments (great for flowcharts)
- **Thickness preview**: A visual indicator shows current thickness when adjusting with mouse wheel
- **Quick tool switching**: Use number keys 1-5 to quickly switch between tools while drawing
- **Multi-monitor drawing**: Draw seamlessly from one screen to another
- **Preserve undo history**: Undo stack is maintained until you clear drawings

### Spotlight Mode

- Press **Ctrl+Shift+S** to toggle the spotlight on/off
- The spotlight follows your cursor automatically at 60 FPS
- Great for focusing audience attention during presentations
- Configure appearance in Settings (radius, ring size, color, opacity)

### System Tray

Right-click the Glowpoint icon in your system tray to:
- Toggle spotlight
- Clear drawings
- Access settings
- View about information
- Quit the application

## Configuration

### Customizing Shortcuts

1. Right-click the system tray icon and select **Settings**
2. Click in any shortcut field
3. Press your desired key combination
4. Click **Save** to apply changes

### Spotlight Settings

| Setting | Description | Range |
|---------|-------------|-------|
| Spotlight Radius | Size of the glow effect | 5-200 pixels |
| Ring Radius | Size of the bright ring | 5-100 pixels |
| Glow Opacity | Brightness/intensity | 0-100% |
| Spotlight Color | Color of the spotlight | Any color |

**Live Preview**: All spotlight settings update in real-time as you adjust them!

### Drawing Settings

| Setting | Description | Range |
|---------|-------------|-------|
| Line Width | Default thickness | 1-20 pixels |
| Tool Shortcuts | Keys for each tool | Any single key |

### Configuration File

Settings are stored in `config.json` in the application directory.

Example `config.json`:
```json
{
  "shortcuts": {
    "toggle_spotlight": "<ctrl>+<shift>+s",
    "draw_blue": "<ctrl>+<shift>+b",
    "draw_red": "<ctrl>+<shift>+r",
    "draw_yellow": "<ctrl>+<shift>+y",
    "draw_green": "<ctrl>+<shift>+g",
    "clear_screen": "<ctrl>+<shift>+c",
    "quit": "<ctrl>+<shift>+q"
  },
  "spotlight": {
    "enabled": true,
    "radius": 80,
    "ring_radius": 40,
    "opacity": 0.7,
    "color": "#FFFF64"
  },
  "drawing": {
    "line_width": 4,
    "colors": {
      "blue": "#2196F3",
      "red": "#F44336",
      "yellow": "#FFEB3B",
      "green": "#4CAF50"
    },
    "tool_shortcuts": {
      "freehand": "1",
      "line": "2",
      "rectangle": "3",
      "arrow": "4",
      "circle": "5"
    }
  }
}
```

## Creating a Distributable Version

Want to share Glowpoint with colleagues who don't have Python installed? You can create a standalone executable!

### Quick Build (Windows)

Simply run the build script:
```bash
build_dist.bat
```

This creates a `Glowpoint_Portable` folder containing:
- `Glowpoint.exe` - Standalone executable (no Python required!)
- `README.txt` - User instructions
- `LICENSE` - License file

**Distribution**: Copy the entire `Glowpoint_Portable` folder to any Windows computer and double-click `Glowpoint.exe` to run!

### Manual Build (All Platforms)

If you prefer manual control or are on Linux/Mac:

1. **Install PyInstaller**:
   ```bash
   pip install pyinstaller
   ```

2. **Create the executable**:
   ```bash
   pyinstaller glowpoint.spec --clean
   ```

3. **Find your executable**:
   - The executable will be in the `dist/` folder
   - On Windows: `dist/Glowpoint.exe`
   - On Linux/Mac: `dist/Glowpoint`

**For detailed distribution instructions, see [DISTRIBUTION.md](DISTRIBUTION.md)**

## Platform Support

| Platform | Status | Notes |
|----------|--------|-------|
| Windows | Fully supported | Best experience on Windows 10/11 |
| Linux | Fully supported | Requires X11 |
| macOS | Supported | May require accessibility permissions |

### macOS Permissions

On macOS, you may need to grant accessibility permissions:
1. Go to System Preferences -> Security & Privacy -> Privacy -> Accessibility
2. Add Python or your Glowpoint executable to the list
3. Grant permission

### Linux Requirements

- X11 display server (Wayland may have limited support)
- Some systems may require `python3-pyqt5` from your package manager

## Use Cases

- **Presentations**: Highlight important points and draw diagrams on the fly
- **Screen Recording**: Make tutorials more engaging with cursor highlighting
- **Online Teaching**: Draw explanations during video calls
- **Code Reviews**: Point out specific areas of code during screen sharing
- **Gaming Streams**: Highlight cursor for better viewer experience
- **Technical Support**: Guide users by pointing and annotating their screen

## Development

### Project Structure

```
Glowpoint/
├── glowpoint.py          # Main application entry point
├── config_manager.py     # Configuration management
├── overlay_window.py     # Transparent overlay window with drawing tools
├── hotkey_manager.py     # Global keyboard shortcuts
├── settings_dialog.py    # Settings UI dialog
├── requirements.txt      # Python dependencies
├── config.json           # User configuration (auto-generated)
├── test_hotkeys.py       # Hotkey testing utility
├── glowpoint.spec        # PyInstaller spec file
├── build_dist.bat        # Windows build script
├── DISTRIBUTION.md       # Distribution guide
└── README.md             # This file
```

### Architecture

- **PyQt5**: GUI framework for overlay window, toolbar, and system tray
- **pynput**: Global keyboard listener for shortcuts
- **QPainter**: High-performance drawing engine with antialiasing
- **Transparent Overlay**: Fullscreen window that stays on top but respects taskbar

### Key Technical Features

- **Click-through Window**: Overlay is transparent to mouse events when not drawing
- **Taskbar-Aware**: Uses available screen geometry to avoid taskbar conflicts
- **Smooth Drawing**: Catmull-Rom spline interpolation for freehand curves
- **60 FPS Updates**: Smooth cursor tracking for spotlight effect
- **Thread-Safe Hotkeys**: pynput runs in background thread with safe Qt signal emission
- **Feathered Rendering**: Multi-layer glow effect for all drawing elements

## Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests
- Improve documentation

## License

This project is open source and available for personal and commercial use.

## Acknowledgments

- Built with [PyQt5](https://www.riverbankcomputing.com/software/pyqt/)
- Keyboard handling by [pynput](https://github.com/moses-palmer/pynput)

## Troubleshooting

### Shortcuts not working

- Make sure the application is running (check system tray)
- Try restarting the application
- Check for conflicting shortcuts with other applications
- **Remote Desktop Users**: Global hotkeys may not work through some remote desktop solutions. Try using Windows RDP or run Glowpoint locally.
- **Test hotkeys**: Run `python test_hotkeys.py` to diagnose hotkey detection issues

### Taskbar Issues (Windows 11)

- Glowpoint now uses available screen geometry to respect the taskbar
- If issues persist, try restarting the application

### Drawing not working on all monitors

- Glowpoint automatically detects and covers all monitors
- If issues persist, try restarting the application
- Check console output for multi-monitor detection messages

### Drawing is laggy

- Close unnecessary applications
- Reduce line width in settings
- Disable spotlight when drawing

### Can't see the system tray icon

- Look in the system tray overflow area (hidden icons)
- Check if the application is running

### Application won't start

- Verify Python 3.7+ is installed: `python --version`
- Check all dependencies are installed: `pip install -r requirements.txt`
- Try running from terminal to see error messages

## Support

If you encounter issues or have questions:
1. Check the troubleshooting section above
2. Review the configuration file for errors
3. Run from terminal to see error messages
4. Check that all dependencies are properly installed

---

**Enjoy using Glowpoint!** If you find it helpful, please share it with others!
