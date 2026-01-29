#!/usr/bin/env python3
"""Glowpoint - Cursor highlighter and screen drawing tool for presentations."""
import sys
from PyQt5.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QAction,
                             QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QFrame, QWidget)
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor, QFont
from PyQt5.QtCore import Qt

from config_manager import ConfigManager
from overlay_window import OverlayWindow
from hotkey_manager import HotkeyManager
from settings_dialog import SettingsDialog, COLORS


class GlowpointApp:
    """Main application class for Glowpoint."""

    def __init__(self):
        """Initialize the application."""
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        # Initialize configuration
        self.config = ConfigManager()

        # Initialize overlay window
        self.overlay = OverlayWindow(self.config)
        self.overlay.show()

        # Initialize hotkey manager
        self.hotkey_manager = HotkeyManager(self.config)
        self._connect_hotkeys()
        self.hotkey_manager.start()

        # Drawing state
        self.drawing_color = None

        # Create system tray icon
        self._create_tray_icon()

    def _connect_hotkeys(self):
        """Connect hotkey signals to handler methods."""
        self.hotkey_manager.spotlight_toggle.connect(self._toggle_spotlight)
        self.hotkey_manager.draw_blue.connect(lambda: self._toggle_drawing("blue"))
        self.hotkey_manager.draw_red.connect(lambda: self._toggle_drawing("red"))
        self.hotkey_manager.draw_yellow.connect(lambda: self._toggle_drawing("yellow"))
        self.hotkey_manager.draw_green.connect(lambda: self._toggle_drawing("green"))
        self.hotkey_manager.clear_screen.connect(self._clear_screen)
        self.hotkey_manager.quit_app.connect(self._quit_application)

        # Connect overlay signals
        self.overlay.mode_changed.connect(self._on_mode_changed)

    def _on_mode_changed(self, mode_name: str):
        """Handle drawing mode change notification.

        Args:
            mode_name: Name of the new drawing mode
        """
        self.tray_icon.showMessage(
            "Drawing Mode",
            f"Tool: {mode_name}",
            QSystemTrayIcon.Information,
            1000
        )

    def _create_tray_icon(self):
        """Create system tray icon and menu."""
        # Create a simple icon
        icon = self._create_icon()

        self.tray_icon = QSystemTrayIcon(icon, self.app)

        # Create tooltip with all hotkeys (compact format to avoid cutoff)
        s = self.config.get_shortcut_display  # shorthand
        tooltip = f"""Glowpoint Shortcuts:
Spotlight: {s('toggle_spotlight')}
Draw: {s('draw_blue')}, {s('draw_red')}, {s('draw_yellow')}, {s('draw_green')}
Clear: {s('clear_screen')} | Quit: {s('quit')}"""
        self.tray_icon.setToolTip(tooltip)

        # Create menu
        menu = QMenu()

        # Spotlight toggle action
        self.spotlight_action = QAction("Spotlight: ON" if self.overlay.spotlight_enabled else "Spotlight: OFF", menu)
        self.spotlight_action.triggered.connect(self._toggle_spotlight)
        menu.addAction(self.spotlight_action)

        menu.addSeparator()

        # Clear screen action
        clear_action = QAction("Clear Drawings", menu)
        clear_action.triggered.connect(self._clear_screen)
        menu.addAction(clear_action)

        menu.addSeparator()

        # Settings action
        settings_action = QAction("Settings", menu)
        settings_action.triggered.connect(self._show_settings)
        menu.addAction(settings_action)

        # About action
        about_action = QAction("About", menu)
        about_action.triggered.connect(self._show_about)
        menu.addAction(about_action)

        menu.addSeparator()

        # Quit action
        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(self._quit_application)
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

        # Show notification on startup
        s = self.config.get_shortcut_display  # shorthand
        self.tray_icon.showMessage(
            "Glowpoint Started",
            f"Hover over icon to see all shortcuts\n"
            f"Spotlight: {s('toggle_spotlight')}\n"
            f"Draw: {s('draw_blue')}, {s('draw_red')}, {s('draw_yellow')}, {s('draw_green')}",
            QSystemTrayIcon.Information,
            3000
        )

    def _create_icon(self):
        """Create application icon.

        Returns:
            QIcon: Application icon
        """
        # Create a simple circular icon
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)

        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw outer circle (glow)
        painter.setBrush(QColor(255, 200, 0, 200))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(4, 4, 56, 56)

        # Draw inner circle
        painter.setBrush(QColor(255, 255, 255))
        painter.drawEllipse(20, 20, 24, 24)

        painter.end()

        return QIcon(pixmap)

    def _toggle_spotlight(self):
        """Toggle spotlight on/off."""
        self.overlay.toggle_spotlight()
        self.spotlight_action.setText("Spotlight: ON" if self.overlay.spotlight_enabled else "Spotlight: OFF")

    def _toggle_drawing(self, color: str):
        """Toggle drawing mode with specified color.

        Args:
            color: Color name (blue, red, yellow)
        """
        print(f"_toggle_drawing called with color: {color}")
        print(f"Current drawing_active: {self.overlay.drawing_active}, current color: {self.drawing_color}")

        if self.overlay.drawing_active and self.drawing_color == color:
            # Stop drawing if same color is pressed again
            print(f"Stopping drawing mode")
            self.overlay.stop_drawing()
            self.drawing_color = None
            self.tray_icon.showMessage(
                "Drawing Mode OFF",
                f"Drawing mode stopped.",
                QSystemTrayIcon.Information,
                1000
            )
        else:
            # Start drawing with new color
            print(f"Starting drawing mode with color: {color}")
            self.overlay.start_drawing(color)
            self.drawing_color = color
            self.tray_icon.showMessage(
                "Drawing Mode ON",
                f"Drawing in {color.upper()}\n"
                f"Tools: 1=Freehand 2=Line 3=Rectangle 4=Arrow 5=Circle\n"
                f"Press color hotkey again or ESC to stop.",
                QSystemTrayIcon.Information,
                2500
            )

        print(f"New drawing_active: {self.overlay.drawing_active}")

    def _clear_screen(self):
        """Clear all drawings."""
        self.overlay.clear_drawings()
        self.tray_icon.showMessage(
            "Drawings Cleared",
            "All drawings have been cleared from the screen.",
            QSystemTrayIcon.Information,
            1000
        )

    def _show_settings(self):
        """Show settings dialog."""
        # Pause hotkeys while settings dialog is open to prevent conflicts
        self.hotkey_manager.stop()

        dialog = SettingsDialog(self.config, self.overlay)
        dialog.settings_changed.connect(self._on_settings_changed)
        dialog.exec_()

        # Resume hotkeys after settings dialog closes
        self.hotkey_manager.reload_hotkeys()

    def _on_settings_changed(self):
        """Handle settings changes."""
        # Reload overlay settings
        self.overlay.spotlight_enabled = self.config.get("spotlight", "enabled")
        self.spotlight_action.setText("Spotlight: ON" if self.overlay.spotlight_enabled else "Spotlight: OFF")

        # Note: Hotkey changes require restart
        # We could reload them, but it's safer to require restart

    def _show_about(self):
        """Show modern about dialog."""
        dialog = AboutDialog(self.config)
        dialog.exec_()


class AboutDialog(QDialog):
    """Modern styled About dialog."""

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self._setup_ui()

    def _setup_ui(self):
        """Set up the about dialog UI."""
        self.setWindowTitle("About Glowpoint")
        self.setFixedSize(480, 580)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['background']};
            }}
            QLabel {{
                color: {COLORS['text']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 24)
        layout.setSpacing(16)

        # App icon and title
        header_layout = QHBoxLayout()
        header_layout.setSpacing(16)

        # Create icon
        icon_label = QLabel()
        pixmap = QPixmap(48, 48)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(255, 200, 0, 200))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(4, 4, 40, 40)
        painter.setBrush(QColor(255, 255, 255))
        painter.drawEllipse(16, 16, 16, 16)
        painter.end()
        icon_label.setPixmap(pixmap)
        header_layout.addWidget(icon_label)

        # Title and version
        title_layout = QVBoxLayout()
        title_layout.setSpacing(4)
        title = QLabel("Glowpoint")
        title.setStyleSheet(f"font-size: 28px; font-weight: bold; color: {COLORS['text']};")
        version = QLabel("Version 1.0.0")
        version.setStyleSheet(f"font-size: 14px; color: {COLORS['text_muted']};")
        title_layout.addWidget(title)
        title_layout.addWidget(version)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Description
        desc = QLabel("A presentation tool that highlights your cursor and lets you draw annotations on screen.")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"font-size: 14px; color: {COLORS['text']}; padding: 8px 0;")
        layout.addWidget(desc)

        # Separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet(f"background-color: {COLORS['border']};")
        sep1.setFixedHeight(1)
        layout.addWidget(sep1)

        # Current shortcuts section
        shortcuts_title = QLabel("Current Shortcuts")
        shortcuts_title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLORS['primary']}; padding-top: 8px;")
        layout.addWidget(shortcuts_title)

        s = self.config.get_shortcut_display
        shortcuts_text = f"""
<table style="color: {COLORS['text']}; font-size: 13px;">
<tr><td style="padding: 4px 16px 4px 0;"><b>Spotlight:</b></td><td>{s('toggle_spotlight')}</td></tr>
<tr><td style="padding: 4px 16px 4px 0;"><b>Draw Blue:</b></td><td>{s('draw_blue')}</td></tr>
<tr><td style="padding: 4px 16px 4px 0;"><b>Draw Red:</b></td><td>{s('draw_red')}</td></tr>
<tr><td style="padding: 4px 16px 4px 0;"><b>Draw Yellow:</b></td><td>{s('draw_yellow')}</td></tr>
<tr><td style="padding: 4px 16px 4px 0;"><b>Draw Green:</b></td><td>{s('draw_green')}</td></tr>
<tr><td style="padding: 4px 16px 4px 0;"><b>Clear:</b></td><td>{s('clear_screen')}</td></tr>
<tr><td style="padding: 4px 16px 4px 0;"><b>Quit:</b></td><td>{s('quit')}</td></tr>
</table>
"""
        shortcuts_label = QLabel(shortcuts_text)
        shortcuts_label.setStyleSheet(f"color: {COLORS['text']};")
        layout.addWidget(shortcuts_label)

        # Tool shortcuts
        tool_shortcuts = self.config.get("drawing", "tool_shortcuts") or {}
        tools_title = QLabel("Drawing Tools")
        tools_title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: {COLORS['primary']}; padding-top: 8px;")
        layout.addWidget(tools_title)

        tools_text = f"""
<table style="color: {COLORS['text']}; font-size: 13px;">
<tr><td style="padding: 4px 16px 4px 0;"><b>{tool_shortcuts.get('freehand', '1')}</b> Freehand</td>
    <td style="padding: 4px 16px 4px 0;"><b>{tool_shortcuts.get('line', '2')}</b> Line</td>
    <td><b>{tool_shortcuts.get('rectangle', '3')}</b> Rectangle</td></tr>
<tr><td style="padding: 4px 16px 4px 0;"><b>{tool_shortcuts.get('arrow', '4')}</b> Arrow</td>
    <td style="padding: 4px 16px 4px 0;"><b>{tool_shortcuts.get('circle', '5')}</b> Circle</td>
    <td></td></tr>
</table>
<p style="margin-top: 8px; color: {COLORS['text_muted']}; font-size: 12px;">
<b>ESC</b> exit drawing | <b>Mouse wheel</b> adjust thickness | <b>Ctrl+Z</b> undo | <b>Ctrl+Shift+Z</b> redo
</p>
"""
        tools_label = QLabel(tools_text)
        tools_label.setStyleSheet(f"color: {COLORS['text']};")
        layout.addWidget(tools_label)

        layout.addStretch()

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['primary']};
                border: none;
                border-radius: 6px;
                padding: 10px 32px;
                color: white;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {COLORS['primary_hover']};
            }}
        """)
        close_btn.clicked.connect(self.accept)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    def _quit_application(self):
        """Quit the application."""
        self.hotkey_manager.stop()
        self.tray_icon.hide()
        self.overlay.close()
        self.app.quit()

    def run(self):
        """Run the application.

        Returns:
            int: Exit code
        """
        return self.app.exec_()


def main():
    """Main entry point."""
    app = GlowpointApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
