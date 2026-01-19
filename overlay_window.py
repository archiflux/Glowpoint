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
        self.current_line_width = None
        self.all_paths: List[Tuple[List[QPoint], str, int]] = []  # path, color, line_width
        self.spotlight_enabled = self.config.get("spotlight", "enabled")
        self.last_cursor_pos = QPoint(0, 0)
        self.last_line_endpoint = None  # For shift+click straight lines

        # Thickness preview
        self.show_thickness_preview = False
        self.thickness_preview_timer = None

        # Shift+click straight line mode
        self.shift_line_start = None
        self.shift_line_preview = None

        self._setup_window()
        self._setup_cursor_timer()
        self._setup_thickness_preview_timer()

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

        # Calculate and set geometry to cover all screens
        self._update_geometry()

        # Connect to screen change signals to handle display reconfiguration
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        if app:
            # Connect to screen added/removed signals
            app.screenAdded.connect(self._on_screen_changed)
            app.screenRemoved.connect(self._on_screen_changed)
            # Connect to primary screen changed signal
            app.primaryScreenChanged.connect(self._on_screen_changed)
            # Also monitor for geometry changes on existing screens
            for screen in app.screens():
                screen.geometryChanged.connect(self._on_screen_changed)

        self.show()

    def _on_screen_changed(self, *args):
        """Handle screen configuration changes (add/remove/resize).

        Args:
            *args: Signal arguments (varies by signal type)
        """
        print("[OverlayWindow] Screen configuration changed, updating geometry...")
        self._update_geometry()

    def _update_geometry(self):
        """Calculate and set window geometry to cover all screens."""
        from PyQt5.QtWidgets import QApplication
        desktop = QApplication.desktop()

        # Calculate bounding rectangle that covers all screens
        x_min = y_min = float('inf')
        x_max = y_max = float('-inf')

        for i in range(desktop.screenCount()):
            screen_geom = desktop.screenGeometry(i)
            x_min = min(x_min, screen_geom.x())
            y_min = min(y_min, screen_geom.y())
            x_max = max(x_max, screen_geom.x() + screen_geom.width())
            y_max = max(y_max, screen_geom.y() + screen_geom.height())

        # Set geometry to cover all screens
        self.setGeometry(int(x_min), int(y_min), int(x_max - x_min), int(y_max - y_min))
        print(f"[OverlayWindow] Covering {desktop.screenCount()} screens: "
              f"{int(x_min)},{int(y_min)} {int(x_max - x_min)}x{int(y_max - y_min)}")

    def _setup_cursor_timer(self):
        """Set up timer for cursor position updates."""
        self.cursor_timer = QTimer()
        self.cursor_timer.timeout.connect(self._update_cursor_position)
        self.cursor_timer.start(16)  # ~60 FPS

    def _setup_thickness_preview_timer(self):
        """Set up timer for thickness preview."""
        self.thickness_preview_timer = QTimer()
        self.thickness_preview_timer.timeout.connect(self._hide_thickness_preview)
        self.thickness_preview_timer.setSingleShot(True)

    def _update_cursor_position(self):
        """Update cursor position for spotlight effect."""
        if self.spotlight_enabled:
            self.last_cursor_pos = QCursor.pos()
            self.update()  # Trigger repaint

    def _hide_thickness_preview(self):
        """Hide the thickness preview indicator."""
        self.show_thickness_preview = False
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
        self.current_line_width = self.config.get("drawing", "line_width")  # Capture current width
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
        # Refresh geometry to ensure we cover all current screens
        self._update_geometry()
        print("[OverlayWindow] Showing with cross cursor")
        self.show()
        self.setCursor(Qt.CrossCursor)
        print("[OverlayWindow] start_drawing complete")

    def stop_drawing(self):
        """Stop drawing mode."""
        if self.drawing_active and self.current_path:
            # Save the current path with its line width
            self.all_paths.append((self.current_path.copy(), self.current_color, self.current_line_width))

        self.drawing_active = False
        self.current_path = []
        self.current_color = None
        self.last_line_endpoint = None

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
        # Refresh geometry to ensure we cover all current screens
        self._update_geometry()
        self.show()
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
            from PyQt5.QtCore import Qt as QtModifier
            # Check if shift is held for straight line mode
            if event.modifiers() & QtModifier.ShiftModifier and self.last_line_endpoint:
                # Draw straight line from last endpoint to current position
                self.current_path = [self.last_line_endpoint, event.pos()]
                self.all_paths.append((self.current_path.copy(), self.current_color))
                self.last_line_endpoint = event.pos()
                self.current_path = []
                self.update()
            else:
                # Normal freehand drawing
                self.current_path = [event.pos()]
                self.last_line_endpoint = None

    def mouseMoveEvent(self, event):
        """Handle mouse move events.

        Args:
            event: Mouse event
        """
        if self.drawing_active and event.buttons() & Qt.LeftButton:
            # Check if in shift+click straight line mode
            if self.shift_line_start is not None:
                self.shift_line_preview = event.pos()
                self.update()
            else:
                # Add point decimation to reduce jaggedness on sharp corners
                # Only add point if it's far enough from the last point
                if len(self.current_path) > 0:
                    last_point = self.current_path[-1]
                    distance = ((event.pos().x() - last_point.x()) ** 2 +
                               (event.pos().y() - last_point.y()) ** 2) ** 0.5
                    # Increased threshold to 8 pixels for smoother lines
                    if distance > 8:
                        self.current_path.append(event.pos())
                else:
                    self.current_path.append(event.pos())
                self.update()

    def mouseReleaseEvent(self, event):
        """Handle mouse release events.

        Args:
            event: Mouse event
        """
        if self.drawing_active and event.button() == Qt.LeftButton:
            if self.current_path and len(self.current_path) > 0:
                self.all_paths.append((self.current_path.copy(), self.current_color))
                # Save last point for shift+click straight lines
                self.last_line_endpoint = self.current_path[-1]
                self.current_path = []
            self.update()

    def keyPressEvent(self, event):
        """Handle key press events.

        Args:
            event: Key event
        """
        from PyQt5.QtCore import Qt as QtKey
        if self.drawing_active and event.key() == QtKey.Key_Escape:
            print("[OverlayWindow] Escape key pressed, stopping drawing")
            self.stop_drawing()

    def wheelEvent(self, event):
        """Handle mouse wheel events for changing line thickness.

        Args:
            event: Wheel event
        """
        if self.drawing_active:
            # Get current line width
            current_width = self.config.get("drawing", "line_width")

            # Adjust based on wheel direction
            delta = event.angleDelta().y()
            if delta > 0:
                # Scroll up - increase thickness
                new_width = min(current_width + 1, 20)
            else:
                # Scroll down - decrease thickness
                new_width = max(current_width - 1, 1)

            # Save new width
            if new_width != current_width:
                self.config.set(new_width, "drawing", "line_width")
                print(f"[OverlayWindow] Line width changed to {new_width}px")
                # Show notification would be nice but we don't have access to tray icon here
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

        # Draw all saved paths with feathering/glow effect
        for path, color, path_line_width in self.all_paths:
            if len(path) >= 1:
                smooth_path = self._create_smooth_path(path)
                self._draw_feathered_path(painter, smooth_path, QColor(color), path_line_width)

        # Draw current path being drawn
        if self.current_path and len(self.current_path) >= 1:
            smooth_path = self._create_smooth_path(self.current_path)
            self._draw_feathered_path(painter, smooth_path, QColor(self.current_color), self.current_line_width)

        # Draw shift+click straight line preview
        if self.shift_line_start is not None and self.shift_line_preview is not None:
            preview_path = QPainterPath()
            preview_path.moveTo(self.shift_line_start)
            preview_path.lineTo(self.shift_line_preview)
            self._draw_feathered_path(painter, preview_path, QColor(self.current_color), self.current_line_width)

        # Draw thickness preview indicator
        if self.show_thickness_preview:
            cursor_pos = QCursor.pos()
            current_line_width = self.config.get("drawing", "line_width")
            radius = current_line_width / 2

            # Draw dashed semi-transparent black ring
            pen = QPen(QColor(0, 0, 0, 128), 2, Qt.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(cursor_pos, int(radius), int(radius))

    def _draw_feathered_path(self, painter: QPainter, path: QPainterPath, color: QColor, line_width: int):
        """Draw a path with feathering/glow effect.

        Args:
            painter: QPainter instance
            path: Path to draw
            color: Color of the line
            line_width: Width of the line
        """
        # Draw outer glow layers (3 layers for subtle feathering)
        glow_layers = [
            (line_width * 2.2, 20),   # Outermost glow, very transparent
            (line_width * 1.6, 40),   # Middle glow
            (line_width * 1.2, 70),   # Inner glow
        ]

        for width_mult, alpha in glow_layers:
            glow_color = QColor(color.red(), color.green(), color.blue(), alpha)
            glow_pen = QPen(glow_color, width_mult, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
            painter.setPen(glow_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)

        # Draw the main line on top
        main_pen = QPen(color, line_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(main_pen)
        painter.setBrush(Qt.NoBrush)
        painter.drawPath(path)

    def _create_smooth_path(self, points: List[QPoint]) -> QPainterPath:
        """Create a smooth curved path from a list of points using Catmull-Rom splines.

        Args:
            points: List of QPoint objects

        Returns:
            QPainterPath: Smoothed path
        """
        path = QPainterPath()

        if len(points) < 1:
            return path

        if len(points) == 1:
            # Single point - create a visible dot
            # The pen width in _draw_feathered_path will make it properly sized
            path.addEllipse(points[0], 2, 2)
            return path

        if len(points) == 2:
            # Just draw a straight line for 2 points
            path.moveTo(points[0])
            path.lineTo(points[1])
            return path

        # Use Catmull-Rom spline for extra smooth curves
        path.moveTo(points[0])

        for i in range(len(points) - 1):
            # Get control points for Catmull-Rom spline
            p0 = points[max(0, i - 1)]
            p1 = points[i]
            p2 = points[min(len(points) - 1, i + 1)]
            p3 = points[min(len(points) - 1, i + 2)]

            # Calculate control points for cubic Bezier
            # Using Catmull-Rom to Bezier conversion
            cp1_x = p1.x() + (p2.x() - p0.x()) / 6.0
            cp1_y = p1.y() + (p2.y() - p0.y()) / 6.0
            cp2_x = p2.x() - (p3.x() - p1.x()) / 6.0
            cp2_y = p2.y() - (p3.y() - p1.y()) / 6.0

            path.cubicTo(
                QPoint(int(cp1_x), int(cp1_y)),
                QPoint(int(cp2_x), int(cp2_y)),
                p2
            )

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
