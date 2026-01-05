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
        self.paint_count = 0  # Debug counter

        print(f"[DEBUG] OverlayWindow initialized. Spotlight enabled: {self.spotlight_enabled}")

        self._setup_window()
        self._setup_cursor_timer()
        print(f"[DEBUG] OverlayWindow setup complete")

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
            self.update()  # Trigger repaint

    def start_drawing(self, color: str):
        """Start drawing mode with specified color.

        Args:
            color: Color name (blue, red, yellow)
        """
        print(f"[DEBUG] start_drawing called with color: {color}")
        self.drawing_active = True
        color_hex = self.config.get("drawing", "colors", color)
        self.current_color = color_hex
        self.current_path = []
        print(f"[DEBUG] Drawing active, color_hex: {color_hex}")

        # Make window accept mouse events
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.showFullScreen()
        self.setCursor(Qt.CrossCursor)
        print(f"[DEBUG] Drawing mode window flags set")

    def stop_drawing(self):
        """Stop drawing mode."""
        if self.drawing_active and self.current_path:
            # Save the current path
            self.all_paths.append((self.current_path.copy(), self.current_color))

        self.drawing_active = False
        self.current_path = []
        self.current_color = None

        # Make window transparent to mouse events again
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
        print(f"[DEBUG] toggle_spotlight called. Current: {self.spotlight_enabled}")
        self.spotlight_enabled = not self.spotlight_enabled
        self.config.set(self.spotlight_enabled, "spotlight", "enabled")
        print(f"[DEBUG] Spotlight now: {self.spotlight_enabled}, calling update()")
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
        self.paint_count += 1
        if self.paint_count % 60 == 1:  # Print every 60 frames (once per second)
            print(f"[DEBUG] paintEvent called (count: {self.paint_count}), spotlight_enabled: {self.spotlight_enabled}")

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw spotlight effect
        if self.spotlight_enabled:
            if self.paint_count % 60 == 1:
                print(f"[DEBUG] Drawing spotlight at {self.last_cursor_pos}")
            self._draw_spotlight(painter)

        # Draw all saved paths
        line_width = self.config.get("drawing", "line_width")
        for path, color in self.all_paths:
            if len(path) > 1:
                pen = QPen(QColor(color), line_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
                painter.setPen(pen)
                painter.setBrush(Qt.NoBrush)

                # Use smoothed path
                smooth_path = self._create_smooth_path(path)
                painter.drawPath(smooth_path)

        # Draw current path being drawn
        if self.current_path and len(self.current_path) > 1:
            pen = QPen(QColor(self.current_color), line_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)

            # Use smoothed path
            smooth_path = self._create_smooth_path(self.current_path)
            painter.drawPath(smooth_path)

    def _create_smooth_path(self, points: List[QPoint]) -> QPainterPath:
        """Create a smooth curved path from a list of points using quadratic Bezier curves.

        Args:
            points: List of QPoint objects

        Returns:
            QPainterPath: Smoothed path
        """
        path = QPainterPath()

        if len(points) < 2:
            return path

        if len(points) == 2:
            # Just draw a straight line for 2 points
            path.moveTo(points[0])
            path.lineTo(points[1])
            return path

        # Start at the first point
        path.moveTo(points[0])

        # For smoothing, we'll use quadratic curves with control points
        # calculated as the midpoint between consecutive points
        for i in range(len(points) - 2):
            # Current point
            p0 = points[i]
            # Next point
            p1 = points[i + 1]
            # Point after next
            p2 = points[i + 2]

            # Calculate control point as the current next point
            # and the end point as the midpoint between p1 and p2
            if i == 0:
                # For the first segment, start from p0 to midpoint of p0-p1 and p1
                path.quadTo(p1, QPoint((p1.x() + p2.x()) // 2, (p1.y() + p2.y()) // 2))
            else:
                # Use quadratic curve with p1 as control point
                path.quadTo(p1, QPoint((p1.x() + p2.x()) // 2, (p1.y() + p2.y()) // 2))

        # Draw the last segment to the final point
        if len(points) > 2:
            path.quadTo(points[-2], points[-1])

        return path

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
