"""Transparent overlay window for cursor highlighting and drawing."""
from PyQt5.QtWidgets import QWidget
from PyQt5.QtCore import Qt, QPoint, QTimer, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QColor, QRadialGradient, QCursor, QPainterPath
from typing import List, Tuple, Optional


class OverlayWindow(QWidget):
    """Transparent overlay window for drawing and cursor highlighting."""

    def __init__(self, config_manager):
        """Initialize overlay window.

        Args:
            config_manager: Configuration manager instance
        """
        super().__init__()
        self.config = config_manager
        self.drawing_active = False
        self.current_color = None
        self.current_path = []
        self.all_paths: List[Tuple[List[QPoint], str]] = []
        self.spotlight_enabled = self.config.get("spotlight", "enabled")
        self.last_cursor_pos = QPoint(0, 0)

        self._setup_window()
        self._setup_cursor_timer()

    def _setup_window(self):
        """Set up window properties."""
        # Make window fullscreen and transparent
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        # Get screen geometry
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen)

        self.showFullScreen()

    def _setup_cursor_timer(self):
        """Set up timer for cursor position updates."""
        self.cursor_timer = QTimer()
        self.cursor_timer.timeout.connect(self._update_cursor_position)
        self.cursor_timer.start(16)  # ~60 FPS

    def _update_cursor_position(self):
        """Update cursor position for spotlight effect."""
        if self.spotlight_enabled:
            self.last_cursor_pos = QCursor.pos()
            self.update()

    def start_drawing(self, color: str):
        """Start drawing mode with specified color.

        Args:
            color: Color name (blue, red, yellow)
        """
        print(f"[OverlayWindow] start_drawing called with color: {color}")
        self.drawing_active = True
        color_hex = self.config.get("drawing", "colors", color)
        self.current_color = color_hex
        self.current_path = []
        print(f"[OverlayWindow] Color hex: {color_hex}, drawing_active: {self.drawing_active}")

        # Make window accept mouse events
        # Must hide before changing flags for them to take effect
        print("[OverlayWindow] Hiding window before flag change")
        self.hide()
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        print("[OverlayWindow] Showing fullscreen with cross cursor")
        self.showFullScreen()
        self.setCursor(Qt.CrossCursor)
        print("[OverlayWindow] start_drawing complete")

    def stop_drawing(self):
        """Stop drawing mode."""
        if self.drawing_active and self.current_path:
            # Save the current path
            self.all_paths.append((self.current_path.copy(), self.current_color))

        self.drawing_active = False
        self.current_path = []
        self.current_color = None

        # Make window transparent to mouse events again
        # Must hide before changing flags for them to take effect
        self.hide()
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool |
            Qt.WindowTransparentForInput
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.showFullScreen()
        self.unsetCursor()
        self.update()

    def clear_drawings(self):
        """Clear all drawings from the screen."""
        self.all_paths.clear()
        self.current_path.clear()
        self.update()

    def toggle_spotlight(self):
        """Toggle cursor spotlight on/off."""
        self.spotlight_enabled = not self.spotlight_enabled
        self.config.set(self.spotlight_enabled, "spotlight", "enabled")
        self.update()

    def mousePressEvent(self, event):
        """Handle mouse press events.

        Args:
            event: Mouse event
        """
        if self.drawing_active and event.button() == Qt.LeftButton:
            self.current_path = [event.pos()]

    def mouseMoveEvent(self, event):
        """Handle mouse move events.

        Args:
            event: Mouse event
        """
        if self.drawing_active and event.buttons() & Qt.LeftButton:
            self.current_path.append(event.pos())
            self.update()

    def mouseReleaseEvent(self, event):
        """Handle mouse release events.

        Args:
            event: Mouse event
        """
        if self.drawing_active and event.button() == Qt.LeftButton:
            if self.current_path:
                self.all_paths.append((self.current_path.copy(), self.current_color))
                self.current_path = []
            self.update()

    def paintEvent(self, event):
        """Paint the overlay.

        Args:
            event: Paint event
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw spotlight effect
        if self.spotlight_enabled:
            self._draw_spotlight(painter)

        # Draw all saved paths
        line_width = self.config.get("drawing", "line_width")
        for path, color in self.all_paths:
            if len(path) > 1:
                pen = QPen(QColor(color), line_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                painter.setPen(pen)

                for i in range(len(path) - 1):
                    painter.drawLine(path[i], path[i + 1])

        # Draw current path being drawn
        if self.current_path and len(self.current_path) > 1:
            pen = QPen(QColor(self.current_color), line_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)

            for i in range(len(self.current_path) - 1):
                painter.drawLine(self.current_path[i], self.current_path[i + 1])

    def _draw_spotlight(self, painter: QPainter):
        """Draw spotlight effect around cursor.

        Args:
            painter: QPainter instance
        """
        radius = self.config.get("spotlight", "radius")
        color_hex = self.config.get("spotlight", "color")
        opacity = self.config.get("spotlight", "opacity")
        base_color = QColor(color_hex)

        # Draw bright glowing circle around cursor with opacity control
        gradient = QRadialGradient(self.last_cursor_pos, radius)
        gradient.setColorAt(0, QColor(base_color.red(), base_color.green(), base_color.blue(), int(180 * opacity)))
        gradient.setColorAt(0.3, QColor(base_color.red(), base_color.green(), base_color.blue(), int(120 * opacity)))
        gradient.setColorAt(0.7, QColor(base_color.red(), base_color.green(), base_color.blue(), int(60 * opacity)))
        gradient.setColorAt(1, QColor(255, 255, 255, 0))  # Transparent edge

        painter.setBrush(gradient)
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(self.last_cursor_pos, radius, radius)

        # Draw bright ring for emphasis
        ring_radius = self.config.get("spotlight", "ring_radius")
        pen = QPen(QColor(base_color.red(), base_color.green(), base_color.blue(), int(200 * opacity)), 3)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(self.last_cursor_pos, ring_radius, ring_radius)
