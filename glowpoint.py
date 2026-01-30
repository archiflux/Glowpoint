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
        else:
            # Start drawing with new color
            print(f"Starting drawing mode with color: {color}")
            self.overlay.start_drawing(color)
            self.drawing_color = color

        print(f"New drawing_active: {self.overlay.drawing_active}")

    def _clear_screen(self):
        """Clear all drawings."""
        self.overlay.clear_drawings()

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


class AboutDialog(QDialog):
    """OLED-optimized About dialog with sophisticated dark theme."""

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self._setup_ui()

    def _setup_ui(self):
        """Set up the about dialog UI."""
        self.setWindowTitle("About Glowpoint")
        self.setFixedSize(420, 520)

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['background']};
            }}
            QLabel {{
                color: {COLORS['text']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 20)
        layout.setSpacing(12)

        # App icon and title
        header_layout = QHBoxLayout()
        header_layout.setSpacing(14)

        # Create icon with OLED-friendly colors
        icon_label = QLabel()
        pixmap = QPixmap(44, 44)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(COLORS['accent']))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, 40, 40)
        painter.setBrush(QColor(COLORS['text']))
        painter.drawEllipse(14, 14, 16, 16)
        painter.end()
        icon_label.setPixmap(pixmap)
        header_layout.addWidget(icon_label)

        # Title and version
        title_layout = QVBoxLayout()
        title_layout.setSpacing(2)
        title = QLabel("Glowpoint")
        title.setStyleSheet(f"font-size: 22px; font-weight: 600; color: {COLORS['text']};")
        version = QLabel("Version 1.0.0")
        version.setStyleSheet(f"font-size: 12px; color: {COLORS['text_secondary']};")
        title_layout.addWidget(title)
        title_layout.addWidget(version)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Description
        desc = QLabel("A presentation tool for cursor highlighting and screen annotations.")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"font-size: 13px; color: {COLORS['text_secondary']}; padding: 4px 0;")
        layout.addWidget(desc)

        # Separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.HLine)
        sep1.setStyleSheet(f"background-color: {COLORS['border']};")
        sep1.setFixedHeight(1)
        layout.addWidget(sep1)

        # Current shortcuts section
        shortcuts_title = QLabel("Shortcuts")
        shortcuts_title.setStyleSheet(f"font-size: 13px; font-weight: 500; color: {COLORS['text_secondary']}; padding-top: 4px;")
        layout.addWidget(shortcuts_title)

        s = self.config.get_shortcut_display
        shortcuts_data = [
            ("Spotlight", s('toggle_spotlight')),
            ("Draw Blue", s('draw_blue')),
            ("Draw Red", s('draw_red')),
            ("Draw Yellow", s('draw_yellow')),
            ("Draw Green", s('draw_green')),
            ("Clear", s('clear_screen')),
            ("Quit", s('quit')),
        ]

        shortcuts_widget = QWidget()
        shortcuts_widget.setStyleSheet(f"background-color: {COLORS['surface']}; border-radius: 6px;")
        shortcuts_layout = QVBoxLayout(shortcuts_widget)
        shortcuts_layout.setContentsMargins(12, 8, 12, 8)
        shortcuts_layout.setSpacing(4)

        for label, shortcut in shortcuts_data:
            row = QHBoxLayout()
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
            key = QLabel(shortcut)
            key.setStyleSheet(f"color: {COLORS['text']}; font-size: 12px;")
            key.setAlignment(Qt.AlignRight)
            row.addWidget(lbl)
            row.addWidget(key)
            shortcuts_layout.addLayout(row)

        layout.addWidget(shortcuts_widget)

        # Tool shortcuts
        tool_shortcuts = self.config.get("drawing", "tool_shortcuts") or {}
        tools_title = QLabel("Drawing Tools")
        tools_title.setStyleSheet(f"font-size: 13px; font-weight: 500; color: {COLORS['text_secondary']}; padding-top: 4px;")
        layout.addWidget(tools_title)

        tools_widget = QWidget()
        tools_widget.setStyleSheet(f"background-color: {COLORS['surface']}; border-radius: 6px;")
        tools_layout = QVBoxLayout(tools_widget)
        tools_layout.setContentsMargins(12, 8, 12, 8)
        tools_layout.setSpacing(4)

        tools_data = [
            (tool_shortcuts.get('freehand', '1'), "Freehand"),
            (tool_shortcuts.get('line', '2'), "Line"),
            (tool_shortcuts.get('rectangle', '3'), "Rectangle"),
            (tool_shortcuts.get('arrow', '4'), "Arrow"),
            (tool_shortcuts.get('circle', '5'), "Circle"),
        ]

        tools_row1 = QHBoxLayout()
        for key, name in tools_data[:3]:
            item = QLabel(f"{key} {name}")
            item.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
            tools_row1.addWidget(item)
        tools_layout.addLayout(tools_row1)

        tools_row2 = QHBoxLayout()
        for key, name in tools_data[3:]:
            item = QLabel(f"{key} {name}")
            item.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 12px;")
            tools_row2.addWidget(item)
        tools_row2.addStretch()
        tools_layout.addLayout(tools_row2)

        # Additional tips
        tips = QLabel("ESC exit · Scroll thickness · Ctrl+Z undo")
        tips.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 11px; padding-top: 4px;")
        tools_layout.addWidget(tips)

        layout.addWidget(tools_widget)

        layout.addStretch()

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_muted']};
                border: 1px solid {COLORS['border_focus']};
                border-radius: 4px;
                padding: 8px 24px;
                color: {COLORS['accent']};
                font-size: 13px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {COLORS['border_focus']};
                color: {COLORS['accent_hover']};
            }}
        """)
        close_btn.clicked.connect(self.accept)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)


def main():
    """Main entry point."""
    app = GlowpointApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
