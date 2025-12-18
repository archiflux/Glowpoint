#!/usr/bin/env python3
"""SpotCursor - Cursor highlighter and screen drawing tool for presentations."""
import sys
from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QAction, QMessageBox
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QColor
from PyQt5.QtCore import Qt

from config_manager import ConfigManager
from overlay_window import OverlayWindow
from hotkey_manager import HotkeyManager
from settings_dialog import SettingsDialog


class SpotCursorApp:
    """Main application class for SpotCursor."""

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

    def _create_tray_icon(self):
        """Create system tray icon and menu."""
        # Create a simple icon
        icon = self._create_icon()

        self.tray_icon = QSystemTrayIcon(icon, self.app)

        # Create tooltip with all hotkeys (compact format to avoid cutoff)
        s = self.config.get_shortcut  # shorthand
        tooltip = f"""SpotCursor Shortcuts:
Spotlight: {s('toggle_spotlight')}
Draw: B/R/Y/G (Ctrl+Shift+B/R/Y/G)
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
        self.tray_icon.showMessage(
            "SpotCursor Started",
            f"Hover over icon to see all shortcuts\n"
            f"Spotlight: {self.config.get_shortcut('toggle_spotlight')}\n"
            f"Draw: {self.config.get_shortcut('draw_blue')}, {self.config.get_shortcut('draw_red')}, "
            f"{self.config.get_shortcut('draw_yellow')}, {self.config.get_shortcut('draw_green')}",
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

        # Draw outer circle (spotlight)
        painter.setBrush(QColor(33, 150, 243, 200))
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
        if self.overlay.drawing_active and self.drawing_color == color:
            # Stop drawing if same color is pressed again
            self.overlay.stop_drawing()
            self.drawing_color = None
        else:
            # Start drawing with new color
            self.overlay.start_drawing(color)
            self.drawing_color = color

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
        dialog = SettingsDialog(self.config, self.overlay)
        dialog.settings_changed.connect(self._on_settings_changed)
        dialog.exec_()

    def _on_settings_changed(self):
        """Handle settings changes."""
        # Reload overlay settings
        self.overlay.spotlight_enabled = self.config.get("spotlight", "enabled")
        self.spotlight_action.setText("Spotlight: ON" if self.overlay.spotlight_enabled else "Spotlight: OFF")

        # Note: Hotkey changes require restart
        # We could reload them, but it's safer to require restart

    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            None,
            "About SpotCursor",
            "<h2>SpotCursor</h2>"
            "<p>Version 1.0.0</p>"
            "<p>A cursor highlighter and screen drawing tool for presentations and screen sharing.</p>"
            "<p><b>Features:</b></p>"
            "<ul>"
            "<li>Spotlight cursor highlighting</li>"
            "<li>Draw on screen in multiple colors</li>"
            "<li>Customizable keyboard shortcuts</li>"
            "<li>Always-on-top annotations</li>"
            "</ul>"
            "<p><b>Default Shortcuts:</b></p>"
            "<ul>"
            f"<li>Toggle Spotlight: {self.config.get_shortcut('toggle_spotlight')}</li>"
            f"<li>Draw Blue: {self.config.get_shortcut('draw_blue')}</li>"
            f"<li>Draw Red: {self.config.get_shortcut('draw_red')}</li>"
            f"<li>Draw Yellow: {self.config.get_shortcut('draw_yellow')}</li>"
            f"<li>Draw Green: {self.config.get_shortcut('draw_green')}</li>"
            f"<li>Clear Screen: {self.config.get_shortcut('clear_screen')}</li>"
            f"<li>Quit: {self.config.get_shortcut('quit')}</li>"
            "</ul>"
            "<p>Right-click the system tray icon to access settings or hover for quick shortcut reference.</p>"
        )

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
    app = SpotCursorApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
