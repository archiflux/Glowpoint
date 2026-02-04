#!/usr/bin/env python3
"""Glowpoint - Cursor highlighter and screen drawing tool for presentations."""
import sys
from PyQt5.QtWidgets import (QApplication, QSystemTrayIcon, QMenu, QAction,
                             QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                             QFrame, QWidget, QGridLayout)
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

        self.config = ConfigManager()
        self.overlay = OverlayWindow(self.config)
        self.overlay.show()

        self.hotkey_manager = HotkeyManager(self.config)
        self._connect_hotkeys()
        self.hotkey_manager.start()

        self.drawing_color = None
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
        icon = self._create_icon()
        self.tray_icon = QSystemTrayIcon(icon, self.app)

        # Compact tooltip that fits Windows constraints (~64 chars per line, ~4 lines)
        s = self.config.get_shortcut_display
        tooltip = (
            f"Glowpoint\n"
            f"Spot:{s('toggle_spotlight')} Draw:B{s('draw_blue')[-1]} R{s('draw_red')[-1]} Y{s('draw_yellow')[-1]} G{s('draw_green')[-1]}\n"
            f"Clear:{s('clear_screen')} Quit:{s('quit')}"
        )
        self.tray_icon.setToolTip(tooltip)

        menu = QMenu()

        self.spotlight_action = QAction("Spotlight: ON" if self.overlay.spotlight_enabled else "Spotlight: OFF", menu)
        self.spotlight_action.triggered.connect(self._toggle_spotlight)
        menu.addAction(self.spotlight_action)

        menu.addSeparator()

        clear_action = QAction("Clear Drawings", menu)
        clear_action.triggered.connect(self._clear_screen)
        menu.addAction(clear_action)

        menu.addSeparator()

        settings_action = QAction("Settings", menu)
        settings_action.triggered.connect(self._show_settings)
        menu.addAction(settings_action)

        about_action = QAction("About", menu)
        about_action.triggered.connect(self._show_about)
        menu.addAction(about_action)

        menu.addSeparator()

        quit_action = QAction("Quit", menu)
        quit_action.triggered.connect(self._quit_application)
        menu.addAction(quit_action)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

    def _create_icon(self):
        """Create application icon."""
        pixmap = QPixmap(64, 64)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(255, 200, 0, 200))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(4, 4, 56, 56)
        painter.setBrush(QColor(255, 255, 255))
        painter.drawEllipse(20, 20, 24, 24)
        painter.end()
        return QIcon(pixmap)

    def _toggle_spotlight(self):
        """Toggle spotlight on/off."""
        self.overlay.toggle_spotlight()
        self.spotlight_action.setText("Spotlight: ON" if self.overlay.spotlight_enabled else "Spotlight: OFF")

    def _toggle_drawing(self, color: str):
        """Toggle drawing mode with specified color."""
        if self.overlay.drawing_active and self.drawing_color == color:
            self.overlay.stop_drawing()
            self.drawing_color = None
        else:
            self.overlay.start_drawing(color)
            self.drawing_color = color

    def _clear_screen(self):
        """Clear all drawings."""
        self.overlay.clear_drawings()

    def _show_settings(self):
        """Show settings dialog."""
        self.hotkey_manager.stop()
        dialog = SettingsDialog(self.config, self.overlay)
        dialog.settings_changed.connect(self._on_settings_changed)
        dialog.exec_()
        self.hotkey_manager.reload_hotkeys()
        self._update_tooltip()

    def _on_settings_changed(self):
        """Handle settings changes."""
        self.overlay.spotlight_enabled = self.config.get("spotlight", "enabled")
        self.spotlight_action.setText("Spotlight: ON" if self.overlay.spotlight_enabled else "Spotlight: OFF")

    def _update_tooltip(self):
        """Update tray tooltip with current shortcuts."""
        s = self.config.get_shortcut_display
        tooltip = (
            f"Glowpoint\n"
            f"Spot:{s('toggle_spotlight')} Draw:B{s('draw_blue')[-1]} R{s('draw_red')[-1]} Y{s('draw_yellow')[-1]} G{s('draw_green')[-1]}\n"
            f"Clear:{s('clear_screen')} Quit:{s('quit')}"
        )
        self.tray_icon.setToolTip(tooltip)

    def _show_about(self):
        """Show about dialog."""
        dialog = AboutDialog(self.config)
        dialog.exec_()

    def _quit_application(self):
        """Quit the application."""
        self.hotkey_manager.stop()
        self.tray_icon.hide()
        self.overlay.close()
        self.app.quit()

    def run(self):
        """Run the application."""
        return self.app.exec_()


class AboutDialog(QDialog):
    """Compact About dialog with dark title bar."""

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self._drag_pos = None
        self._setup_ui()

    def _setup_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(320, 360)

        container = QWidget(self)
        container.setGeometry(0, 0, 320, 360)
        container.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['background']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
            }}
        """)

        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Title bar
        title_bar = QWidget()
        title_bar.setFixedHeight(28)
        title_bar.setStyleSheet(f"background-color: {COLORS['title_bar']}; border-radius: 6px 6px 0 0;")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 6, 0)

        title = QLabel("About")
        title.setStyleSheet(f"color: {COLORS['text']}; font-size: 11px; font-weight: 500;")
        title_layout.addWidget(title)
        title_layout.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(20, 20)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['text_secondary']};
                border: none;
                font-size: 12px;
            }}
            QPushButton:hover {{
                color: {COLORS['text']};
                background-color: {COLORS['surface_hover']};
                border-radius: 3px;
            }}
        """)
        close_btn.clicked.connect(self.accept)
        title_layout.addWidget(close_btn)
        main_layout.addWidget(title_bar)

        # Content
        content = QWidget()
        content.setStyleSheet(f"background-color: {COLORS['background']};")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(14, 10, 14, 10)
        content_layout.setSpacing(8)

        # Header
        header = QHBoxLayout()
        header.setSpacing(10)

        icon = QLabel()
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(COLORS['accent']))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(2, 2, 28, 28)
        painter.setBrush(QColor(COLORS['text']))
        painter.drawEllipse(10, 10, 12, 12)
        painter.end()
        icon.setPixmap(pixmap)
        header.addWidget(icon)

        title_col = QVBoxLayout()
        title_col.setSpacing(0)
        name = QLabel("Glowpoint")
        name.setStyleSheet(f"color: {COLORS['text']}; font-size: 16px; font-weight: 600;")
        ver = QLabel("v1.0.0")
        ver.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px;")
        title_col.addWidget(name)
        title_col.addWidget(ver)
        header.addLayout(title_col)
        header.addStretch()
        content_layout.addLayout(header)

        # Description
        desc = QLabel("Cursor highlighter and screen annotation tool")
        desc.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10px;")
        content_layout.addWidget(desc)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"background-color: {COLORS['border']};")
        sep.setFixedHeight(1)
        content_layout.addWidget(sep)

        # Shortcuts section
        section_lbl = QLabel("SHORTCUTS")
        section_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 9px; font-weight: 500;")
        content_layout.addWidget(section_lbl)

        s = self.config.get_shortcut_display
        shortcuts = [
            ("Spotlight", s('toggle_spotlight')),
            ("Blue", s('draw_blue')),
            ("Red", s('draw_red')),
            ("Yellow", s('draw_yellow')),
            ("Green", s('draw_green')),
            ("Clear", s('clear_screen')),
            ("Quit", s('quit')),
        ]

        grid = QGridLayout()
        grid.setSpacing(2)
        for i, (label, key) in enumerate(shortcuts):
            row, col = divmod(i, 2)
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10px;")
            lbl.setFixedWidth(50)
            val = QLabel(key)
            val.setStyleSheet(f"color: {COLORS['text']}; font-size: 10px;")
            h = QHBoxLayout()
            h.setSpacing(4)
            h.addWidget(lbl)
            h.addWidget(val)
            h.addStretch()
            grid.addLayout(h, row, col)
        content_layout.addLayout(grid)

        # Tools section
        tools_lbl = QLabel("TOOLS")
        tools_lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 9px; font-weight: 500; padding-top: 4px;")
        content_layout.addWidget(tools_lbl)

        ts = self.config.get("drawing", "tool_shortcuts") or {}
        tools_text = f"{ts.get('freehand','1')}=Free {ts.get('line','2')}=Line {ts.get('rectangle','3')}=Rect {ts.get('arrow','4')}=Arrow {ts.get('circle','5')}=Circle"
        tools = QLabel(tools_text)
        tools.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10px;")
        content_layout.addWidget(tools)

        tips = QLabel("ESC=exit  Scroll=thickness  Ctrl+Z=undo")
        tips.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 9px;")
        content_layout.addWidget(tips)

        content_layout.addStretch()

        # Close button
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        close = QPushButton("Close")
        close.setCursor(Qt.PointingHandCursor)
        close.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['accent_muted']};
                border: 1px solid {COLORS['border_focus']};
                border-radius: 3px;
                padding: 4px 14px;
                color: {COLORS['accent']};
                font-size: 10px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['border_focus']};
            }}
        """)
        close.clicked.connect(self.accept)
        btn_row.addWidget(close)
        content_layout.addLayout(btn_row)

        main_layout.addWidget(content)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.pos().y() < 28:
            self._drag_pos = event.globalPos() - self.pos()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


def main():
    """Main entry point."""
    app = GlowpointApp()
    sys.exit(app.run())


if __name__ == "__main__":
    main()
