# Glowpoint 🎯

A lightweight cursor highlighter and screen drawing tool perfect for presentations, screen sharing, and tutorials. Highlight your cursor with an attractive spotlight effect and draw annotations on your screen in real-time!

## ✨ Features

- **Spotlight Cursor Highlighting**: Draw attention to your cursor with a beautiful spotlight effect
- **Screen Drawing**: Draw on your screen in multiple colors (blue, red, yellow)
- **Global Keyboard Shortcuts**: Control everything with customizable keyboard shortcuts
- **Always-on-Top Annotations**: Drawings stay visible over all windows
- **Lightweight & Efficient**: Minimal resource usage, no admin rights required
- **Customizable**: Configure shortcuts, colors, line width, and spotlight settings
- **System Tray Integration**: Quick access to all features from the system tray

## 🚀 Installation

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

## 🎮 Usage

### Default Keyboard Shortcuts

- **Ctrl+Shift+S**: Toggle spotlight on/off
- **Ctrl+Shift+B**: Draw in blue
- **Ctrl+Shift+R**: Draw in red
- **Ctrl+Shift+Y**: Draw in yellow
- **Ctrl+Shift+G**: Draw in green
- **Ctrl+Shift+C**: Clear all drawings
- **Ctrl+Shift+Q**: Quit application

**Tip**: Hover over the system tray icon to see all current shortcuts!

### How to Draw

1. Press a drawing shortcut (e.g., **Ctrl+Shift+B** for blue)
2. Click and drag your mouse to draw
3. Release the mouse button to finish the line
4. Press the same shortcut again to stop drawing mode
5. Press **Ctrl+Shift+C** to clear all drawings

### Spotlight Mode

- Press **Ctrl+Shift+S** to toggle the spotlight on/off
- The spotlight follows your cursor automatically
- Great for focusing audience attention during presentations

### System Tray

Right-click the Glowpoint icon in your system tray to:
- Toggle spotlight
- Clear drawings
- Access settings
- View keyboard shortcuts
- Quit the application

## ⚙️ Configuration

### Customizing Shortcuts

1. Right-click the system tray icon and select **Settings**
2. Click in any shortcut field
3. Press your desired key combination
4. Click **Save** and restart the application

### Adjusting Spotlight Settings

In the Settings dialog, you can adjust:
- **Spotlight Radius**: Size of the spotlight glow (50-200 pixels)
- **Ring Radius**: Size of the bright ring around cursor (10-100 pixels)
- **Spotlight Color**: Choose any color for your spotlight using the color picker
- **Glow Opacity**: Controls the intensity/brightness of the spotlight glow (0-100%)

**Live Preview**: All spotlight settings update in real-time as you adjust them - move your cursor to see the changes immediately!

### Adjusting Drawing Settings

- **Line Width**: Thickness of drawn lines (1-20 pixels)

### Configuration File

Settings are stored in `config.json` in the application directory. You can manually edit this file if needed.

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
    }
  }
}
```

## 📦 Creating a Distributable Version

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

## 🖥️ Platform Support

- **Windows**: Fully supported ✅
- **Linux**: Fully supported ✅ (requires X11)
- **macOS**: Supported ✅ (may require accessibility permissions)

### macOS Permissions

On macOS, you may need to grant accessibility permissions:
1. Go to System Preferences → Security & Privacy → Privacy → Accessibility
2. Add Python or your Glowpoint executable to the list
3. Grant permission

### Linux Requirements

- X11 display server (Wayland may have limited support)
- Some systems may require `python3-pyqt5` from your package manager

## 🎯 Use Cases

- **Presentations**: Highlight important points and draw diagrams on the fly
- **Screen Recording**: Make tutorials more engaging with cursor highlighting
- **Online Teaching**: Draw explanations during video calls
- **Code Reviews**: Point out specific areas of code during screen sharing
- **Gaming Streams**: Highlight cursor for better viewer experience

## 🛠️ Development

### Project Structure

```
Glowpoint/
├── glowpoint.py          # Main application entry point
├── config_manager.py      # Configuration management
├── overlay_window.py      # Transparent overlay for drawing
├── hotkey_manager.py      # Global keyboard shortcuts
├── settings_dialog.py     # Settings UI
├── requirements.txt       # Python dependencies
├── config.json           # User configuration (auto-generated)
└── README.md             # This file
```

### Architecture

- **PyQt5**: GUI framework for overlay window and system tray
- **pynput**: Global keyboard listener for shortcuts
- **QPainter**: High-performance drawing engine
- **Transparent Overlay**: Fullscreen window that stays on top

### Key Features Implementation

- **Click-through Window**: Overlay is transparent to mouse events when not drawing
- **Always-on-Top**: Uses Qt window flags to stay above all windows
- **Smooth Drawing**: 60 FPS refresh rate for cursor tracking
- **Global Shortcuts**: Works even when application is not focused

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Report bugs
- Suggest new features
- Submit pull requests
- Improve documentation

## 📝 License

This project is open source and available for personal and commercial use.

## 🙏 Acknowledgments

- Built with [PyQt5](https://www.riverbankcomputing.com/software/pyqt/)
- Keyboard handling by [pynput](https://github.com/moses-palmer/pynput)

## 💡 Tips & Tricks

1. **Performance**: Disable spotlight when not needed for better performance
2. **Multiple Colors**: You can quickly switch between colors while drawing
3. **Precision**: Use a lower line width for detailed annotations
4. **Visibility**: Adjust spotlight opacity based on screen brightness
5. **Quick Clear**: Keep the clear shortcut handy for fast cleanup

## ❓ Troubleshooting

### Shortcuts not working
- Make sure the application is running (check system tray)
- Try restarting the application
- Check for conflicting shortcuts with other applications

### Drawing is laggy
- Close unnecessary applications
- Reduce line width in settings
- Disable spotlight when drawing

### Can't see the system tray icon
- Look in the system tray overflow area (hidden icons)
- Check if the application is running: `ps aux | grep glowpoint`

### Application won't start
- Verify Python 3.7+ is installed: `python --version`
- Check all dependencies are installed: `pip install -r requirements.txt`
- Try running from terminal to see error messages

## 📧 Support

If you encounter issues or have questions:
1. Check the troubleshooting section
2. Review the configuration file for errors
3. Run from terminal to see error messages
4. Check that all dependencies are properly installed

---

**Enjoy using Glowpoint!** ⭐ If you find it helpful, please share it with others!
