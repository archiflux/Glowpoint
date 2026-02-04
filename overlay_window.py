"""Transparent overlay window for cursor highlighting and drawing."""
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QToolButton, QApplication
from PyQt5.QtCore import Qt, QPoint, QTimer, pyqtSignal, QRectF, QSize
from PyQt5.QtGui import QPainter, QPen, QColor, QRadialGradient, QCursor, QPainterPath, QPolygonF, QIcon, QPixmap, QFont
from typing import List, Tuple, Optional
from enum import Enum
import math


class DrawingMode(Enum):
    """Drawing tool modes."""
    FREEHAND = 1
    LINE = 2
    RECTANGLE = 3
    ARROW = 4
    CIRCLE = 5


class DrawingToolbar(QWidget):
    """Floating toolbar for drawing tool selection with OLED-optimized dark theme."""

    # Signal emitted when a tool is selected
    tool_selected = pyqtSignal(DrawingMode)

    # OLED-optimized colors
    COLORS = {
        "background": "rgba(0, 0, 0, 230)",
        "surface": "rgba(13, 13, 13, 255)",
        "surface_hover": "rgba(30, 30, 30, 255)",
        "border": "rgba(31, 31, 31, 255)",
        "text": "rgba(212, 212, 212, 255)",
        "text_secondary": "rgba(133, 133, 133, 255)",
        "accent": "rgba(74, 158, 255, 255)",
        "accent_muted": "rgba(26, 58, 92, 255)",
    }

    def __init__(self, config_manager, parent=None):
        """Initialize the toolbar.

        Args:
            config_manager: Configuration manager for shortcuts
            parent: Parent widget
        """
        super().__init__(parent)
        self.config = config_manager
        self.current_mode = DrawingMode.FREEHAND
        self.buttons = {}

        self._setup_ui()

    def _setup_ui(self):
        """Set up the toolbar UI."""
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(3)

        # Tool definitions: (mode, symbol, name, config_key)
        tools = [
            (DrawingMode.FREEHAND, "✏", "Freehand", "freehand"),
            (DrawingMode.LINE, "╱", "Line", "line"),
            (DrawingMode.RECTANGLE, "▢", "Rectangle", "rectangle"),
            (DrawingMode.ARROW, "➔", "Arrow", "arrow"),
            (DrawingMode.CIRCLE, "○", "Circle", "circle"),
        ]

        for mode, symbol, name, config_key in tools:
            shortcut = self.config.get("drawing", "tool_shortcuts", config_key) or config_key[0]
            btn = QToolButton()
            btn.setText(symbol)
            btn.setFont(QFont("Segoe UI Symbol", 13))
            btn.setFixedSize(32, 32)
            btn.setToolTip(f"{name} ({shortcut})")
            btn.setCheckable(True)
            btn.setStyleSheet(f"""
                QToolButton {{
                    background-color: {self.COLORS['surface']};
                    border: 1px solid {self.COLORS['border']};
                    border-radius: 4px;
                    color: {self.COLORS['text_secondary']};
                }}
                QToolButton:hover {{
                    background-color: {self.COLORS['surface_hover']};
                    color: {self.COLORS['text']};
                }}
                QToolButton:checked {{
                    background-color: {self.COLORS['accent_muted']};
                    border: 1px solid {self.COLORS['accent']};
                    color: {self.COLORS['accent']};
                }}
            """)
            btn.clicked.connect(lambda checked, m=mode: self._on_tool_clicked(m))
            layout.addWidget(btn)
            self.buttons[mode] = btn

        # Set initial selection
        self.buttons[DrawingMode.FREEHAND].setChecked(True)

        self.adjustSize()

    def _on_tool_clicked(self, mode: DrawingMode):
        """Handle tool button click.

        Args:
            mode: The drawing mode selected
        """
        self.set_mode(mode)
        self.tool_selected.emit(mode)

    def set_mode(self, mode: DrawingMode):
        """Set the current drawing mode.

        Args:
            mode: The drawing mode to set
        """
        self.current_mode = mode
        for m, btn in self.buttons.items():
            btn.setChecked(m == mode)

    def position_at_bottom_right(self):
        """Position the toolbar at bottom-right of the primary screen."""
        screen = QApplication.primaryScreen()
        if screen:
            screen_geom = screen.availableGeometry()
            x = screen_geom.right() - self.width() - 16
            y = screen_geom.bottom() - self.height() - 16
            self.move(x, y)

    def paintEvent(self, event):
        """Paint the toolbar background.

        Args:
            event: Paint event
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw rounded rectangle background - true black for OLED
        painter.setBrush(QColor(0, 0, 0, 245))
        painter.setPen(QPen(QColor(31, 31, 31, 255), 1))
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -1, -1), 6, 6)


class OverlayWindow(QWidget):
    """Transparent overlay window for drawing and cursor highlighting."""

    # Signal emitted when drawing mode changes
    mode_changed = pyqtSignal(str)  # Emits mode name

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
        self.all_paths: List[Tuple[List[QPoint], str, int, DrawingMode]] = []  # path, color, line_width, mode
        self.spotlight_enabled = self.config.get("spotlight", "enabled")
        self.last_cursor_pos = QPoint(0, 0)
        self.last_line_endpoint = None  # For shift+click straight lines

        # Thickness preview
        self.show_thickness_preview = False
        self.thickness_preview_timer = None

        # Shift+click straight line mode
        self.shift_line_start = None
        self.shift_line_preview = None

        # Drawing mode (freehand, line, rectangle, arrow)
        self.drawing_mode = DrawingMode.FREEHAND
        self.shape_start_pos = None  # Start position for shapes (rect, arrow, line)

        # Undo/redo stack
        self.undo_stack = []

        # Drawing toolbar
        self.toolbar = DrawingToolbar(self.config)
        self.toolbar.tool_selected.connect(self._on_toolbar_tool_selected)
        self.toolbar.hide()

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
        """Calculate and set window geometry to cover all screens.

        Uses availableGeometry() to respect system reserved areas like
        taskbars and docks, preventing the overlay from interfering with
        the Windows 11 taskbar behavior.
        """
        from PyQt5.QtWidgets import QApplication
        app = QApplication.instance()
        screens = app.screens()

        # Calculate bounding rectangle that covers available area of all screens
        # Using availableGeometry() to respect taskbar/dock areas
        x_min = y_min = float('inf')
        x_max = y_max = float('-inf')

        for screen in screens:
            # availableGeometry() excludes taskbars, docks, etc.
            screen_geom = screen.availableGeometry()
            x_min = min(x_min, screen_geom.x())
            y_min = min(y_min, screen_geom.y())
            x_max = max(x_max, screen_geom.x() + screen_geom.width())
            y_max = max(y_max, screen_geom.y() + screen_geom.height())

        # Set geometry to cover available area of all screens
        self.setGeometry(int(x_min), int(y_min), int(x_max - x_min), int(y_max - y_min))
        print(f"[OverlayWindow] Covering {len(screens)} screens (available area): "
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
        # Grab keyboard focus so we receive key events (1-4 for tools, Escape, Ctrl+Z, etc.)
        self.activateWindow()
        self.raise_()
        self.setFocus()

        # Show the toolbar
        self.toolbar.set_mode(self.drawing_mode)
        self.toolbar.position_at_bottom_right()
        self.toolbar.show()
        self.toolbar.raise_()  # Ensure toolbar is above overlay
        self.toolbar.activateWindow()  # Give toolbar initial focus for clicking
        print("[OverlayWindow] start_drawing complete")

    def stop_drawing(self):
        """Stop drawing mode."""
        if self.drawing_active and self.current_path:
            # Save the current path with its line width and mode
            self.all_paths.append((self.current_path.copy(), self.current_color, self.current_line_width, self.drawing_mode))

        self.drawing_active = False
        self.current_path = []
        self.current_color = None
        self.last_line_endpoint = None
        self.shape_start_pos = None

        # Hide the toolbar
        self.toolbar.hide()

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

    def _on_toolbar_tool_selected(self, mode: DrawingMode):
        """Handle tool selection from toolbar.

        Args:
            mode: The drawing mode selected
        """
        self.drawing_mode = mode
        print(f"[OverlayWindow] Tool selected from toolbar: {mode.name}")
        # Refocus the overlay window to receive keyboard events
        self.activateWindow()
        self.setFocus()

    def _is_point_in_toolbar(self, global_pos: QPoint) -> bool:
        """Check if a global point is within the toolbar area.

        Args:
            global_pos: Global screen position

        Returns:
            True if point is within toolbar, False otherwise
        """
        if self.toolbar.isVisible():
            toolbar_geom = self.toolbar.geometry()
            return toolbar_geom.contains(global_pos)
        return False

    def mousePressEvent(self, event):
        """Handle mouse press events.

        Args:
            event: Mouse event
        """
        # Check if click is on the toolbar - if so, forward the click to toolbar
        if self._is_point_in_toolbar(event.globalPos()):
            # Find which button was clicked and trigger it
            for mode, btn in self.toolbar.buttons.items():
                btn_global_geom = btn.rect()
                btn_global_geom.moveTopLeft(btn.mapToGlobal(btn.rect().topLeft()))
                if btn_global_geom.contains(event.globalPos()):
                    btn.click()
                    return
            return

        if self.drawing_active and event.button() == Qt.LeftButton:
            from PyQt5.QtCore import Qt as QtModifier

            if self.drawing_mode == DrawingMode.FREEHAND:
                # Check if shift is held for straight line mode
                if event.modifiers() & QtModifier.ShiftModifier and self.last_line_endpoint:
                    # Draw straight line from last endpoint to current position
                    self.current_path = [self.last_line_endpoint, event.pos()]
                    self.all_paths.append((self.current_path.copy(), self.current_color, self.current_line_width, DrawingMode.LINE))
                    self.last_line_endpoint = event.pos()
                    self.current_path = []
                    self.update()
                else:
                    # Normal freehand drawing
                    self.current_path = [event.pos()]
                    self.last_line_endpoint = None
                    self.update()  # Draw dot immediately on click

            elif self.drawing_mode in (DrawingMode.LINE, DrawingMode.RECTANGLE, DrawingMode.ARROW, DrawingMode.CIRCLE):
                # For shape tools, store start position
                self.shape_start_pos = event.pos()
                self.current_path = [event.pos()]
                self.update()  # Draw dot immediately on click

    def mouseMoveEvent(self, event):
        """Handle mouse move events.

        Args:
            event: Mouse event
        """
        if self.drawing_active and event.buttons() & Qt.LeftButton:
            if self.drawing_mode == DrawingMode.FREEHAND:
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

            elif self.drawing_mode in (DrawingMode.LINE, DrawingMode.RECTANGLE, DrawingMode.ARROW, DrawingMode.CIRCLE):
                # For shape tools, update end position for preview
                if self.shape_start_pos:
                    self.current_path = [self.shape_start_pos, event.pos()]
                    self.update()

    def mouseReleaseEvent(self, event):
        """Handle mouse release events.

        Args:
            event: Mouse event
        """
        if self.drawing_active and event.button() == Qt.LeftButton:
            if self.drawing_mode == DrawingMode.FREEHAND:
                if self.current_path and len(self.current_path) > 0:
                    self.all_paths.append((self.current_path.copy(), self.current_color, self.current_line_width, DrawingMode.FREEHAND))
                    # Save last point for shift+click straight lines
                    self.last_line_endpoint = self.current_path[-1]
                    self.current_path = []

            elif self.drawing_mode in (DrawingMode.LINE, DrawingMode.RECTANGLE, DrawingMode.ARROW, DrawingMode.CIRCLE):
                # Save the shape
                if self.shape_start_pos and len(self.current_path) >= 2:
                    self.all_paths.append((self.current_path.copy(), self.current_color, self.current_line_width, self.drawing_mode))
                self.shape_start_pos = None
                self.current_path = []

            self.update()

    def _key_matches_shortcut(self, key: int, shortcut: str) -> bool:
        """Check if a key code matches a shortcut string.

        Args:
            key: Qt key code
            shortcut: Shortcut string (e.g., "1", "a", "F1")

        Returns:
            True if the key matches the shortcut
        """
        from PyQt5.QtCore import Qt as QtKey
        if not shortcut:
            return False

        shortcut = shortcut.upper()

        # Map shortcut strings to Qt key codes
        key_map = {
            "1": (QtKey.Key_1, 0x01000051),
            "2": (QtKey.Key_2, 0x01000052),
            "3": (QtKey.Key_3, 0x01000053),
            "4": (QtKey.Key_4, 0x01000054),
            "5": (QtKey.Key_5, 0x01000055),
            "6": (QtKey.Key_6, 0x01000056),
            "7": (QtKey.Key_7, 0x01000057),
            "8": (QtKey.Key_8, 0x01000058),
            "9": (QtKey.Key_9, 0x01000059),
            "0": (QtKey.Key_0, 0x01000050),
            "A": (QtKey.Key_A,), "B": (QtKey.Key_B,), "C": (QtKey.Key_C,),
            "D": (QtKey.Key_D,), "E": (QtKey.Key_E,), "F": (QtKey.Key_F,),
            "G": (QtKey.Key_G,), "H": (QtKey.Key_H,), "I": (QtKey.Key_I,),
            "J": (QtKey.Key_J,), "K": (QtKey.Key_K,), "L": (QtKey.Key_L,),
            "M": (QtKey.Key_M,), "N": (QtKey.Key_N,), "O": (QtKey.Key_O,),
            "P": (QtKey.Key_P,), "Q": (QtKey.Key_Q,), "R": (QtKey.Key_R,),
            "S": (QtKey.Key_S,), "T": (QtKey.Key_T,), "U": (QtKey.Key_U,),
            "V": (QtKey.Key_V,), "W": (QtKey.Key_W,), "X": (QtKey.Key_X,),
            "Y": (QtKey.Key_Y,), "Z": (QtKey.Key_Z,),
        }

        if shortcut in key_map:
            return key in key_map[shortcut]
        return False

    def keyPressEvent(self, event):
        """Handle key press events.

        Args:
            event: Key event
        """
        from PyQt5.QtCore import Qt as QtKey
        key = event.key()
        # Debug: print all key presses to diagnose issues
        print(f"[OverlayWindow] Key pressed: {key} (hex: {hex(key)}), modifiers: {int(event.modifiers())}")

        if self.drawing_active:
            if key == QtKey.Key_Escape:
                print("[OverlayWindow] Escape key pressed, stopping drawing")
                self.stop_drawing()
            elif key == QtKey.Key_Z and event.modifiers() == (QtKey.ControlModifier | QtKey.ShiftModifier):
                # Ctrl+Shift+Z = Redo
                if self.redo():
                    print("[OverlayWindow] Redo performed")
                    self.mode_changed.emit("Redo")
            elif key == QtKey.Key_Z and event.modifiers() == QtKey.ControlModifier:
                # Ctrl+Z = Undo
                if self.undo():
                    print("[OverlayWindow] Undo performed")
                    self.mode_changed.emit("Undo")
            else:
                # Check tool shortcuts from config
                shortcuts = self.config.get("drawing", "tool_shortcuts") or {}
                tool_map = [
                    ("freehand", DrawingMode.FREEHAND, "Freehand"),
                    ("line", DrawingMode.LINE, "Line"),
                    ("rectangle", DrawingMode.RECTANGLE, "Rectangle"),
                    ("arrow", DrawingMode.ARROW, "Arrow"),
                    ("circle", DrawingMode.CIRCLE, "Circle"),
                ]
                for config_key, mode, name in tool_map:
                    shortcut = shortcuts.get(config_key, "")
                    if self._key_matches_shortcut(key, shortcut):
                        self.drawing_mode = mode
                        self.toolbar.set_mode(mode)
                        print(f"[OverlayWindow] Switched to {mode.name} mode")
                        self.mode_changed.emit(f"{name} ({shortcut})")
                        break

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

            # Save new width and update current line width for future strokes
            if new_width != current_width:
                self.config.set(new_width, "drawing", "line_width")
                self.current_line_width = new_width  # Update for next stroke
                print(f"[OverlayWindow] Line width changed to {new_width}px")
                # Show thickness preview indicator for 1 second
                self.show_thickness_preview = True
                self.thickness_preview_timer.start(1000)  # Hide after 1 second
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
        for path, color, path_line_width, mode in self.all_paths:
            if len(path) >= 1:
                painter_path = self._create_path_for_mode(path, mode, path_line_width)
                sharp_corners = (mode == DrawingMode.RECTANGLE)
                self._draw_feathered_path(painter, painter_path, QColor(color), path_line_width, sharp_corners)

        # Draw current path being drawn
        if self.current_path and len(self.current_path) >= 1 and self.current_color:
            painter_path = self._create_path_for_mode(self.current_path, self.drawing_mode, self.current_line_width or 4)
            sharp_corners = (self.drawing_mode == DrawingMode.RECTANGLE)
            self._draw_feathered_path(painter, painter_path, QColor(self.current_color), self.current_line_width, sharp_corners)

        # Draw shift+click straight line preview
        if self.shift_line_start is not None and self.shift_line_preview is not None:
            preview_path = QPainterPath()
            preview_path.moveTo(self.shift_line_start)
            preview_path.lineTo(self.shift_line_preview)
            self._draw_feathered_path(painter, preview_path, QColor(self.current_color), self.current_line_width)

        # Draw thickness preview indicator (like Blender's brush size indicator)
        if self.show_thickness_preview and self.drawing_active:
            cursor_pos = QCursor.pos()
            current_line_width = self.config.get("drawing", "line_width") or 4
            # Use the line width as diameter (radius = line_width / 2 for the actual stroke)
            # But also show the glow extent (roughly 2.2x the line width)
            inner_radius = current_line_width / 2
            outer_radius = current_line_width * 1.1  # Show approximate glow extent

            # Draw outer dashed circle (glow extent) - white with black outline for visibility
            pen = QPen(QColor(255, 255, 255, 200), 1, Qt.DashLine)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(cursor_pos, int(outer_radius), int(outer_radius))

            # Draw inner solid circle (actual line width)
            pen = QPen(QColor(255, 255, 255, 255), 2, Qt.SolidLine)
            painter.setPen(pen)
            painter.drawEllipse(cursor_pos, int(inner_radius), int(inner_radius))

            # Draw text showing the size
            painter.setPen(QColor(255, 255, 255, 255))
            painter.setFont(QFont("Arial", 10, QFont.Bold))
            text_pos = QPoint(cursor_pos.x() + int(outer_radius) + 5, cursor_pos.y() + 5)
            painter.drawText(text_pos, f"{current_line_width}px")

    def _draw_feathered_path(self, painter: QPainter, path: QPainterPath, color: QColor, line_width: int, sharp_corners: bool = False):
        """Draw a path with feathering/glow effect.

        Args:
            painter: QPainter instance
            path: Path to draw
            color: Color of the line
            line_width: Width of the line
            sharp_corners: If True, use MiterJoin for sharp corners (for rectangles)
        """
        # Use MiterJoin for sharp corners (rectangles), RoundJoin for curves
        join_style = Qt.MiterJoin if sharp_corners else Qt.RoundJoin
        cap_style = Qt.SquareCap if sharp_corners else Qt.RoundCap

        # Draw outer glow layers (3 layers for subtle feathering)
        glow_layers = [
            (line_width * 2.2, 20),   # Outermost glow, very transparent
            (line_width * 1.6, 40),   # Middle glow
            (line_width * 1.2, 70),   # Inner glow
        ]

        for width_mult, alpha in glow_layers:
            glow_color = QColor(color.red(), color.green(), color.blue(), alpha)
            glow_pen = QPen(glow_color, width_mult, Qt.SolidLine, cap_style, join_style)
            painter.setPen(glow_pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)

        # Draw the main line on top
        main_pen = QPen(color, line_width, Qt.SolidLine, cap_style, join_style)
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
            # Single point - create a visible dot using ellipse
            # This ensures the dot is visible immediately on click
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

    def _create_path_for_mode(self, points: List[QPoint], mode: DrawingMode, line_width: int = 4) -> QPainterPath:
        """Create a path based on the drawing mode.

        Args:
            points: List of QPoint objects
            mode: The drawing mode
            line_width: Line width for scaling (used by arrow)

        Returns:
            QPainterPath: Path for the given mode
        """
        if mode == DrawingMode.FREEHAND:
            return self._create_smooth_path(points)
        elif mode == DrawingMode.LINE:
            return self._create_line_path(points)
        elif mode == DrawingMode.RECTANGLE:
            return self._create_rectangle_path(points)
        elif mode == DrawingMode.ARROW:
            return self._create_arrow_path(points, line_width)
        elif mode == DrawingMode.CIRCLE:
            return self._create_circle_path(points)
        else:
            return self._create_smooth_path(points)

    def _create_line_path(self, points: List[QPoint]) -> QPainterPath:
        """Create a straight line path (no smoothing).

        Args:
            points: List of QPoint objects (expects 2 points)

        Returns:
            QPainterPath: Straight line path
        """
        path = QPainterPath()

        if len(points) < 1:
            return path

        if len(points) == 1:
            # Single point - create a visible dot
            path.addEllipse(points[0], 2, 2)
            return path

        # Draw straight line from first to last point
        path.moveTo(points[0])
        path.lineTo(points[-1])
        return path

    def _create_rectangle_path(self, points: List[QPoint]) -> QPainterPath:
        """Create a rectangle path with sharp corners (no smoothing).

        Args:
            points: List of QPoint objects (expects 2 points: start and end)

        Returns:
            QPainterPath: Rectangle path
        """
        path = QPainterPath()

        if len(points) < 1:
            return path

        if len(points) == 1:
            # Single point - create a visible dot
            path.addEllipse(points[0], 2, 2)
            return path

        # Create rectangle from two corner points
        p1, p2 = points[0], points[-1]
        x = min(p1.x(), p2.x())
        y = min(p1.y(), p2.y())
        w = abs(p2.x() - p1.x())
        h = abs(p2.y() - p1.y())

        # Use addRect for sharp corners (not addRoundedRect)
        path.addRect(x, y, w, h)
        return path

    def _create_arrow_path(self, points: List[QPoint], line_width: int = 4) -> QPainterPath:
        """Create an arrow path from start to end point.

        Args:
            points: List of QPoint objects (expects 2 points: start and end)
            line_width: Line width for scaling the arrowhead

        Returns:
            QPainterPath: Arrow path with arrowhead
        """
        path = QPainterPath()

        if len(points) < 1:
            return path

        if len(points) == 1:
            # Single point - create a visible dot
            path.addEllipse(points[0], 2, 2)
            return path

        # Draw line from first to last point
        p1, p2 = points[0], points[-1]
        path.moveTo(p1)
        path.lineTo(p2)

        # Calculate arrowhead - scale with line width
        arrow_size = max(line_width * 3, 12)  # Scale with line width, minimum 12
        angle = math.atan2(p2.y() - p1.y(), p2.x() - p1.x())

        # Calculate arrowhead points
        arrow_angle = math.pi / 6  # 30 degrees

        # Left side of arrowhead
        left_x = p2.x() - arrow_size * math.cos(angle - arrow_angle)
        left_y = p2.y() - arrow_size * math.sin(angle - arrow_angle)

        # Right side of arrowhead
        right_x = p2.x() - arrow_size * math.cos(angle + arrow_angle)
        right_y = p2.y() - arrow_size * math.sin(angle + arrow_angle)

        # Draw arrowhead lines
        path.moveTo(p2)
        path.lineTo(int(left_x), int(left_y))
        path.moveTo(p2)
        path.lineTo(int(right_x), int(right_y))

        return path

    def _create_circle_path(self, points: List[QPoint]) -> QPainterPath:
        """Create a circle path from center to edge point.

        Args:
            points: List of QPoint objects (expects 2 points: center and edge)

        Returns:
            QPainterPath: Circle path
        """
        path = QPainterPath()

        if len(points) < 1:
            return path

        if len(points) == 1:
            # Single point - create a visible dot
            path.addEllipse(points[0], 2, 2)
            return path

        # Create circle from center to edge point
        center, edge = points[0], points[-1]
        dx = edge.x() - center.x()
        dy = edge.y() - center.y()
        radius = int(math.sqrt(dx * dx + dy * dy))

        if radius < 2:
            path.addEllipse(center, 2, 2)
            return path

        path.addEllipse(center, radius, radius)
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
