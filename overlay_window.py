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
        self.undo_stack: List[Tuple[List[QPoint], str, int]] = []  # Stack for redo
        self.spotlight_enabled = self.config.get("spotlight", "enabled")
        self.last_cursor_pos = QPoint(0, 0)
        self.last_line_endpoint = None  # For shift+click straight lines

        # Thickness preview
        self.show_thickness_preview = False
        self.thickness_preview_timer = None

        # Shift+click straight line mode
        self.shift_line_start = None
        self.shift_line_preview = None

        # Shape drawing modes (Alt+click = circle, Ctrl+click = rect, Ctrl+Shift+click = arrow)
        self.shape_mode = None  # None, "circle", "rect", "arrow"
        self.shape_start = None  # Starting point for shape
        self.shape_current = None  # Current mouse position for preview

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
        elif self.drawing_active:
            # Still need to repaint when drawing is active (even without spotlight)
            self.update()

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
            self.undo_stack.clear()  # Clear redo stack when new path is added

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
        self.undo_stack.clear()
        self.update()

    def undo(self):
        """Undo the last drawn line."""
        if self.all_paths:
            # Move the last path to undo stack for potential redo
            undone_path = self.all_paths.pop()
            self.undo_stack.append(undone_path)
            print(f"[OverlayWindow] Undo: removed path, {len(self.all_paths)} paths remaining")
            self.update()
            return True
        return False

    def redo(self):
        """Redo the last undone line."""
        if self.undo_stack:
            # Restore the last undone path
            restored_path = self.undo_stack.pop()
            self.all_paths.append(restored_path)
            print(f"[OverlayWindow] Redo: restored path, {len(self.all_paths)} paths total")
            self.update()
            return True
        return False

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
            # Capture current line width at stroke start
            self.current_line_width = self.config.get("drawing", "line_width")

            # Check modifiers for different drawing modes (order matters!)
            has_ctrl = event.modifiers() & QtModifier.ControlModifier
            has_shift = event.modifiers() & QtModifier.ShiftModifier
            has_alt = event.modifiers() & QtModifier.AltModifier

            if has_ctrl and has_shift and self.last_line_endpoint:
                # Ctrl+Shift+Click = Arrow from last endpoint
                self.shape_mode = "arrow"
                self.shape_start = self.last_line_endpoint
                self.shape_current = event.pos()
                self.update()
            elif has_ctrl:
                # Ctrl+Click = Rectangle
                self.shape_mode = "rect"
                self.shape_start = event.pos()
                self.shape_current = event.pos()
                self.update()
            elif has_alt:
                # Alt+Click = Circle (centered on click)
                self.shape_mode = "circle"
                self.shape_start = event.pos()
                self.shape_current = event.pos()
                self.update()
            elif has_shift and self.last_line_endpoint:
                # Shift+Click = Straight line from last endpoint (instant commit)
                self.current_path = [self.last_line_endpoint, event.pos()]
                self.all_paths.append((self.current_path.copy(), self.current_color, self.current_line_width))
                self.undo_stack.clear()  # Clear redo stack when new path is added
                self.last_line_endpoint = event.pos()
                self.current_path = []
                self.update()
            else:
                # Normal freehand drawing
                self.shape_mode = None
                self.current_path = [event.pos()]
                self.last_line_endpoint = None
                self.update()  # Immediately show the dot on mouse press

    def mouseMoveEvent(self, event):
        """Handle mouse move events.

        Args:
            event: Mouse event
        """
        if self.drawing_active and event.buttons() & Qt.LeftButton:
            # Check if in shape drawing mode
            if self.shape_mode is not None:
                self.shape_current = event.pos()
                self.update()
            # Check if in shift+click straight line mode
            elif self.shift_line_start is not None:
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
            # Handle shape finalization
            if self.shape_mode == "circle" and self.shape_start and self.shape_current:
                # Create circle path points
                circle_points = self._create_circle_points(self.shape_start, self.shape_current)
                if circle_points:
                    self.all_paths.append((circle_points, self.current_color, self.current_line_width))
                    self.undo_stack.clear()
                    self.last_line_endpoint = self.shape_current
                self.shape_mode = None
                self.shape_start = None
                self.shape_current = None
                self.update()
            elif self.shape_mode == "rect" and self.shape_start and self.shape_current:
                # Create rectangle path points
                rect_points = self._create_rect_points(self.shape_start, self.shape_current)
                if rect_points:
                    self.all_paths.append((rect_points, self.current_color, self.current_line_width))
                    self.undo_stack.clear()
                    self.last_line_endpoint = self.shape_current
                self.shape_mode = None
                self.shape_start = None
                self.shape_current = None
                self.update()
            elif self.shape_mode == "arrow" and self.shape_start and self.shape_current:
                # Create arrow path points (line + arrowhead)
                arrow_points = self._create_arrow_points(self.shape_start, self.shape_current)
                if arrow_points:
                    self.all_paths.append((arrow_points, self.current_color, self.current_line_width))
                    self.undo_stack.clear()
                    self.last_line_endpoint = self.shape_current
                self.shape_mode = None
                self.shape_start = None
                self.shape_current = None
                self.update()
            elif self.current_path and len(self.current_path) > 0:
                self.all_paths.append((self.current_path.copy(), self.current_color, self.current_line_width))
                self.undo_stack.clear()  # Clear redo stack when new path is added
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

        # Handle Ctrl+Z (undo) and Ctrl+Shift+Z (redo) - works in drawing mode
        if self.drawing_active:
            if event.key() == QtKey.Key_Z and event.modifiers() & QtKey.ControlModifier:
                if event.modifiers() & QtKey.ShiftModifier:
                    # Ctrl+Shift+Z = Redo
                    print("[OverlayWindow] Ctrl+Shift+Z pressed, redo")
                    self.redo()
                else:
                    # Ctrl+Z = Undo
                    print("[OverlayWindow] Ctrl+Z pressed, undo")
                    self.undo()
                return
            elif event.key() == QtKey.Key_Escape:
                print("[OverlayWindow] Escape key pressed, stopping drawing")
                self.stop_drawing()
                return

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
                # Check if this is an arrow (special marker: 3 points with last being (-1, -1))
                if len(path) == 3 and path[2].x() == -1 and path[2].y() == -1:
                    self._draw_arrow(painter, path[0], path[1], QColor(color), path_line_width)
                else:
                    smooth_path = self._create_smooth_path(path)
                    self._draw_feathered_path(painter, smooth_path, QColor(color), path_line_width)

        # Draw current path being drawn
        if self.current_path and len(self.current_path) >= 1:
            smooth_path = self._create_smooth_path(self.current_path)
            self._draw_feathered_path(painter, smooth_path, QColor(self.current_color), self.current_line_width)

        # Draw shape previews
        if self.shape_mode and self.shape_start and self.shape_current:
            color = QColor(self.current_color)
            if self.shape_mode == "circle":
                self._draw_circle_preview(painter, self.shape_start, self.shape_current, color, self.current_line_width)
            elif self.shape_mode == "rect":
                self._draw_rect_preview(painter, self.shape_start, self.shape_current, color, self.current_line_width)
            elif self.shape_mode == "arrow":
                self._draw_arrow(painter, self.shape_start, self.shape_current, color, self.current_line_width)

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

    def _draw_circle_preview(self, painter: QPainter, center: QPoint, edge: QPoint, color: QColor, line_width: int):
        """Draw a circle preview centered on 'center' with radius to 'edge'.

        Args:
            painter: QPainter instance
            center: Center point of circle
            edge: Point on edge (determines radius)
            color: Color of the circle
            line_width: Width of the line
        """
        import math
        dx = edge.x() - center.x()
        dy = edge.y() - center.y()
        radius = int(math.sqrt(dx * dx + dy * dy))

        if radius < 2:
            return

        # Create circle path
        path = QPainterPath()
        path.addEllipse(center, radius, radius)
        self._draw_feathered_path(painter, path, color, line_width)

    def _draw_rect_preview(self, painter: QPainter, corner1: QPoint, corner2: QPoint, color: QColor, line_width: int):
        """Draw a rectangle preview from corner1 to corner2.

        Args:
            painter: QPainter instance
            corner1: First corner
            corner2: Opposite corner
            color: Color of the rectangle
            line_width: Width of the line
        """
        from PyQt5.QtCore import QRectF

        x1, y1 = corner1.x(), corner1.y()
        x2, y2 = corner2.x(), corner2.y()

        if abs(x2 - x1) < 2 and abs(y2 - y1) < 2:
            return

        # Create rectangle path
        path = QPainterPath()
        rect = QRectF(min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
        path.addRect(rect)
        self._draw_feathered_path(painter, path, color, line_width)

    def _draw_arrow(self, painter: QPainter, start: QPoint, end: QPoint, color: QColor, line_width: int):
        """Draw an arrow with line and filled arrowhead.

        Args:
            painter: QPainter instance
            start: Start point of arrow
            end: End point (tip of arrowhead)
            color: Color of the arrow
            line_width: Width of the line
        """
        import math

        dx = end.x() - start.x()
        dy = end.y() - start.y()
        length = math.sqrt(dx * dx + dy * dy)

        if length < 2:
            return

        # Normalize direction
        nx = dx / length
        ny = dy / length

        # Arrowhead size proportional to line width (matching screenshot style)
        head_length = max(line_width * 4, 15)
        head_width = max(line_width * 2.5, 10)

        # Calculate arrowhead base point
        base_x = end.x() - nx * head_length
        base_y = end.y() - ny * head_length

        # Draw the line (from start to base of arrowhead) with feathering
        line_path = QPainterPath()
        line_path.moveTo(start)
        line_path.lineTo(QPoint(int(base_x), int(base_y)))
        self._draw_feathered_path(painter, line_path, color, line_width)

        # Perpendicular direction for arrowhead width
        perp_x = -ny
        perp_y = nx

        left_x = base_x + perp_x * head_width
        left_y = base_y + perp_y * head_width
        right_x = base_x - perp_x * head_width
        right_y = base_y - perp_y * head_width

        # Draw arrowhead with glow effect
        head_path = QPainterPath()
        head_path.moveTo(end)
        head_path.lineTo(QPoint(int(left_x), int(left_y)))
        head_path.lineTo(QPoint(int(right_x), int(right_y)))
        head_path.closeSubpath()

        # Draw glow layers for arrowhead
        glow_layers = [
            (2.2, 20),
            (1.6, 40),
            (1.2, 70),
        ]

        for scale, alpha in glow_layers:
            glow_color = QColor(color.red(), color.green(), color.blue(), alpha)
            painter.setPen(QPen(glow_color, line_width * scale, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            painter.setBrush(glow_color)
            painter.drawPath(head_path)

        # Draw solid arrowhead
        painter.setPen(QPen(color, 1))
        painter.setBrush(color)
        painter.drawPath(head_path)

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
            # Single point - create a tiny line segment that renders as a dot with round caps
            # Using moveTo + lineTo to the same point creates a proper dot with RoundCap
            path.moveTo(points[0])
            path.lineTo(points[0])
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

    def _create_circle_points(self, center: QPoint, edge: QPoint) -> List[QPoint]:
        """Create points for a circle centered on 'center' with radius to 'edge'.

        Args:
            center: Center point of circle
            edge: Point on edge of circle (determines radius)

        Returns:
            List of QPoint forming the circle
        """
        import math
        dx = edge.x() - center.x()
        dy = edge.y() - center.y()
        radius = math.sqrt(dx * dx + dy * dy)

        if radius < 2:
            return []

        # Generate points around the circle (more points for smoother circle)
        num_points = max(36, int(radius / 2))
        points = []
        for i in range(num_points + 1):  # +1 to close the circle
            angle = 2 * math.pi * i / num_points
            x = center.x() + radius * math.cos(angle)
            y = center.y() + radius * math.sin(angle)
            points.append(QPoint(int(x), int(y)))

        return points

    def _create_rect_points(self, corner1: QPoint, corner2: QPoint) -> List[QPoint]:
        """Create points for a rectangle from corner1 to corner2.

        Args:
            corner1: First corner of rectangle
            corner2: Opposite corner of rectangle

        Returns:
            List of QPoint forming the rectangle
        """
        x1, y1 = corner1.x(), corner1.y()
        x2, y2 = corner2.x(), corner2.y()

        if abs(x2 - x1) < 2 and abs(y2 - y1) < 2:
            return []

        # Create rectangle points (5 points to close the shape)
        return [
            QPoint(x1, y1),
            QPoint(x2, y1),
            QPoint(x2, y2),
            QPoint(x1, y2),
            QPoint(x1, y1),  # Close the rectangle
        ]

    def _create_arrow_points(self, start: QPoint, end: QPoint) -> List[QPoint]:
        """Create points for an arrow from start to end.

        The arrow is a straight line with a simple arrowhead at the end,
        scaled proportionally to the line thickness.

        Args:
            start: Start point of arrow
            end: End point (tip of arrowhead)

        Returns:
            List of QPoint forming the arrow (special format for arrow rendering)
        """
        # Return special marker for arrow - we'll handle it in paintEvent
        # Store as [start, end, marker] where marker indicates arrow type
        return [start, end, QPoint(-1, -1)]  # Special marker for arrow

    def _create_arrow_path(self, start: QPoint, end: QPoint, line_width: int) -> QPainterPath:
        """Create a QPainterPath for an arrow with arrowhead.

        Args:
            start: Start point of arrow line
            end: End point (tip of arrowhead)
            line_width: Width of the line (used to scale arrowhead)

        Returns:
            QPainterPath for the complete arrow
        """
        import math
        path = QPainterPath()

        dx = end.x() - start.x()
        dy = end.y() - start.y()
        length = math.sqrt(dx * dx + dy * dy)

        if length < 2:
            return path

        # Normalize direction
        nx = dx / length
        ny = dy / length

        # Arrowhead size proportional to line width (like the screenshot)
        head_length = max(line_width * 4, 15)
        head_width = max(line_width * 2.5, 10)

        # Calculate arrowhead base point (where head meets line)
        base_x = end.x() - nx * head_length
        base_y = end.y() - ny * head_length

        # Calculate the two outer points of the arrowhead
        perp_x = -ny  # Perpendicular direction
        perp_y = nx

        left_x = base_x + perp_x * head_width
        left_y = base_y + perp_y * head_width
        right_x = base_x - perp_x * head_width
        right_y = base_y - perp_y * head_width

        # Draw the line (from start to base of arrowhead)
        path.moveTo(start)
        path.lineTo(QPoint(int(base_x), int(base_y)))

        # Draw the arrowhead as a filled triangle
        # We'll return separate paths for line and head
        return path

    def _create_arrowhead_path(self, start: QPoint, end: QPoint, line_width: int) -> QPainterPath:
        """Create a QPainterPath for just the arrowhead triangle.

        Args:
            start: Start point of arrow line
            end: End point (tip of arrowhead)
            line_width: Width of the line (used to scale arrowhead)

        Returns:
            QPainterPath for the arrowhead triangle
        """
        import math
        path = QPainterPath()

        dx = end.x() - start.x()
        dy = end.y() - start.y()
        length = math.sqrt(dx * dx + dy * dy)

        if length < 2:
            return path

        # Normalize direction
        nx = dx / length
        ny = dy / length

        # Arrowhead size proportional to line width
        head_length = max(line_width * 4, 15)
        head_width = max(line_width * 2.5, 10)

        # Calculate arrowhead base point
        base_x = end.x() - nx * head_length
        base_y = end.y() - ny * head_length

        # Perpendicular direction
        perp_x = -ny
        perp_y = nx

        left_x = base_x + perp_x * head_width
        left_y = base_y + perp_y * head_width
        right_x = base_x - perp_x * head_width
        right_y = base_y - perp_y * head_width

        # Create arrowhead triangle
        path.moveTo(end)
        path.lineTo(QPoint(int(left_x), int(left_y)))
        path.lineTo(QPoint(int(right_x), int(right_y)))
        path.closeSubpath()

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
