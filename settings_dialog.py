"""Settings dialog for configuring shortcuts and preferences."""
import math
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QGroupBox, QFormLayout,
                             QSlider, QFrame, QWidget, QScrollArea, QGridLayout)
from PyQt5.QtCore import Qt, pyqtSignal, QPoint, QRectF
from PyQt5.QtGui import QColor, QFont, QPainter, QConicalGradient, QRadialGradient, QPen, QBrush


# Sophisticated OLED-optimized dark theme
COLORS = {
    "background": "#000000",
    "surface": "#0a0a0a",
    "surface_elevated": "#141414",
    "surface_hover": "#1a1a1a",
    "text": "#d4d4d4",
    "text_secondary": "#808080",
    "text_dim": "#505050",
    "accent": "#4a9eff",
    "accent_hover": "#6bb3ff",
    "accent_muted": "#1a3a5c",
    "border": "#1a1a1a",
    "border_focus": "#2d4a6a",
    "title_bar": "#0a0a0a",
}

# Preset spotlight colors
PRESET_COLORS = [
    "#FFEE58", "#66BB6A", "#4DD0E1", "#BA68C8",
    "#FF8A65", "#F06292", "#81C784", "#7986CB",
]


class NoScrollSlider(QSlider):
    """Slider that ignores mouse wheel events."""

    def wheelEvent(self, event):
        event.ignore()


class ColorWheel(QWidget):
    """Custom color wheel picker widget."""

    color_changed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(140, 140)
        self._hue = 0
        self._saturation = 1.0
        self._value = 1.0
        self._dragging_wheel = False
        self._dragging_triangle = False
        self.setCursor(Qt.CrossCursor)

    def set_color(self, color_hex: str):
        """Set the current color."""
        color = QColor(color_hex)
        self._hue = color.hsvHue() if color.hsvHue() >= 0 else 0
        self._saturation = color.hsvSaturationF()
        self._value = color.valueF()
        self.update()

    def get_color(self) -> str:
        """Get the current color as hex string."""
        color = QColor.fromHsvF(self._hue / 360.0, self._saturation, self._value)
        return color.name()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        center = self.rect().center()
        outer_radius = min(self.width(), self.height()) // 2 - 2
        inner_radius = outer_radius - 16

        # Draw hue wheel
        for i in range(360):
            color = QColor.fromHsvF(i / 360.0, 1.0, 1.0)
            painter.setPen(QPen(color, 2))
            angle = math.radians(i)
            x1 = center.x() + inner_radius * math.cos(angle)
            y1 = center.y() - inner_radius * math.sin(angle)
            x2 = center.x() + outer_radius * math.cos(angle)
            y2 = center.y() - outer_radius * math.sin(angle)
            painter.drawLine(int(x1), int(y1), int(x2), int(y2))

        # Draw inner circle (saturation/value area)
        painter.setBrush(QColor.fromHsvF(self._hue / 360.0, 1.0, 1.0))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(center, inner_radius - 4, inner_radius - 4)

        # Gradient overlays for saturation and value
        sat_gradient = QRadialGradient(center, inner_radius - 4)
        sat_gradient.setColorAt(0, QColor(255, 255, 255, 255))
        sat_gradient.setColorAt(1, QColor(255, 255, 255, 0))
        painter.setBrush(sat_gradient)
        painter.drawEllipse(center, inner_radius - 4, inner_radius - 4)

        val_gradient = QRadialGradient(center, inner_radius - 4)
        val_gradient.setColorAt(0, QColor(0, 0, 0, 0))
        val_gradient.setColorAt(1, QColor(0, 0, 0, 255))
        painter.setBrush(val_gradient)
        painter.drawEllipse(center, inner_radius - 4, inner_radius - 4)

        # Draw hue indicator on wheel
        hue_angle = math.radians(self._hue)
        hue_radius = (inner_radius + outer_radius) / 2
        hue_x = center.x() + hue_radius * math.cos(hue_angle)
        hue_y = center.y() - hue_radius * math.sin(hue_angle)
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setBrush(QColor.fromHsvF(self._hue / 360.0, 1.0, 1.0))
        painter.drawEllipse(QPoint(int(hue_x), int(hue_y)), 5, 5)

        # Draw saturation/value indicator
        sv_radius = (inner_radius - 4) * self._saturation
        sv_x = center.x() + sv_radius * (1 - self._value) * math.cos(hue_angle + math.pi)
        sv_y = center.y() - sv_radius * (1 - self._value) * math.sin(hue_angle + math.pi)
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setBrush(QColor.fromHsvF(self._hue / 360.0, self._saturation, self._value))
        painter.drawEllipse(QPoint(int(center.x()), int(center.y())), 4, 4)

    def mousePressEvent(self, event):
        self._update_color_from_pos(event.pos())

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton:
            self._update_color_from_pos(event.pos())

    def _update_color_from_pos(self, pos):
        center = self.rect().center()
        dx = pos.x() - center.x()
        dy = center.y() - pos.y()
        distance = math.sqrt(dx * dx + dy * dy)

        outer_radius = min(self.width(), self.height()) // 2 - 2
        inner_radius = outer_radius - 16

        if distance > inner_radius - 4:
            # On the hue wheel
            self._hue = (math.degrees(math.atan2(dy, dx)) + 360) % 360
        else:
            # In the center - adjust saturation based on distance
            self._saturation = min(1.0, distance / (inner_radius - 4))
            self._value = 1.0 - (distance / (inner_radius - 4)) * 0.3

        self.update()
        self.color_changed.emit(self.get_color())


class ShortcutRecorder(QLineEdit):
    """Widget for recording keyboard shortcuts."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setPlaceholderText("Click...")
        self.recording = False
        self.setFixedHeight(24)
        self._apply_style()

    def _apply_style(self):
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 3px;
                padding: 2px 6px;
                color: {COLORS['text']};
                font-size: 11px;
            }}
            QLineEdit:hover {{
                background-color: {COLORS['surface_elevated']};
            }}
            QLineEdit:focus {{
                border-color: {COLORS['accent']};
            }}
        """)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if not self.recording:
            self.recording = True
            self.setText("")
            self.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {COLORS['surface_elevated']};
                    border: 1px solid {COLORS['accent']};
                    border-radius: 3px;
                    padding: 2px 6px;
                    color: {COLORS['accent']};
                    font-size: 11px;
                }}
            """)

    def focusOutEvent(self, event):
        super().focusOutEvent(event)
        self.recording = False
        self._apply_style()

    def keyPressEvent(self, event):
        if not self.recording:
            return
        event.accept()
        key = event.key()
        modifiers = event.modifiers()

        if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
            return

        parts = []
        if modifiers & Qt.ControlModifier:
            parts.append("<ctrl>")
        if modifiers & Qt.ShiftModifier:
            parts.append("<shift>")
        if modifiers & Qt.AltModifier:
            parts.append("<alt>")
        if modifiers & Qt.MetaModifier:
            parts.append("<cmd>")

        key_text = None
        if Qt.Key_A <= key <= Qt.Key_Z:
            key_text = chr(key).lower()
        elif Qt.Key_0 <= key <= Qt.Key_9:
            key_text = chr(key)
        elif event.text() and event.text().isprintable():
            key_text = event.text().lower()
        else:
            key_name = {
                Qt.Key_Escape: "esc", Qt.Key_Tab: "tab",
                Qt.Key_Space: "space", Qt.Key_Return: "enter", Qt.Key_Enter: "enter",
            }.get(key)
            if key_name:
                key_text = f"<{key_name}>"

        if key_text:
            parts.append(key_text)

        if len(parts) >= 2 or (len(parts) == 1 and not parts[0].startswith("<")):
            self.setText("+".join(parts))
            self.recording = False
            self._apply_style()


class ColorPresetButton(QPushButton):
    """A clickable color preset button."""

    color_selected = pyqtSignal(str)

    def __init__(self, color_hex: str, parent=None):
        super().__init__(parent)
        self.color_hex = color_hex
        self.setFixedSize(22, 22)
        self.setCursor(Qt.PointingHandCursor)
        self._selected = False
        self._update_style()
        self.clicked.connect(lambda: self.color_selected.emit(self.color_hex))

    def _update_style(self):
        border = f"2px solid {COLORS['accent']}" if self._selected else f"1px solid {COLORS['border']}"
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.color_hex};
                border: {border};
                border-radius: 3px;
            }}
            QPushButton:hover {{
                border: 1px solid {COLORS['text_secondary']};
            }}
        """)

    def set_selected(self, selected: bool):
        self._selected = selected
        self._update_style()


class SettingsDialog(QDialog):
    """Settings dialog with dark title bar."""

    settings_changed = pyqtSignal()

    def __init__(self, config_manager, overlay=None, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self.overlay = overlay
        self.shortcut_inputs = {}
        self.spotlight_color = "#FFFF64"
        self.preset_buttons = []
        self._drag_pos = None
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(400, 520)

        # Main container with border
        container = QWidget(self)
        container.setGeometry(0, 0, 400, 520)
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

        # Custom title bar
        title_bar = QWidget()
        title_bar.setFixedHeight(32)
        title_bar.setStyleSheet(f"background-color: {COLORS['title_bar']}; border-radius: 6px 6px 0 0;")
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(12, 0, 8, 0)

        title_label = QLabel("Settings")
        title_label.setStyleSheet(f"color: {COLORS['text']}; font-size: 12px; font-weight: 500;")
        title_layout.addWidget(title_label)
        title_layout.addStretch()

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                color: {COLORS['text_secondary']};
                border: none;
                font-size: 14px;
            }}
            QPushButton:hover {{
                color: {COLORS['text']};
                background-color: {COLORS['surface_hover']};
                border-radius: 4px;
            }}
        """)
        close_btn.clicked.connect(self.reject)
        title_layout.addWidget(close_btn)
        main_layout.addWidget(title_bar)

        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: {COLORS['background']};
                border: none;
            }}
            QScrollBar:vertical {{
                background: {COLORS['background']};
                width: 5px;
            }}
            QScrollBar::handle:vertical {{
                background: {COLORS['surface_elevated']};
                border-radius: 2px;
                min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                height: 0; background: none;
            }}
        """)

        content = QWidget()
        content.setStyleSheet(f"background-color: {COLORS['background']};")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(12, 8, 12, 8)
        content_layout.setSpacing(8)

        # Sections
        content_layout.addWidget(self._create_shortcuts_section())
        content_layout.addWidget(self._create_spotlight_section())
        content_layout.addWidget(self._create_drawing_section())
        content_layout.addWidget(self._create_tool_shortcuts_section())
        content_layout.addStretch()

        scroll.setWidget(content)
        main_layout.addWidget(scroll)

        # Button bar
        main_layout.addWidget(self._create_button_bar())

    def _create_section_label(self, text):
        label = QLabel(text)
        label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10px; font-weight: 500; padding: 4px 0 2px 0;")
        return label

    def _create_shortcuts_section(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(self._create_section_label("KEYBOARD SHORTCUTS"))

        grid = QGridLayout()
        grid.setSpacing(4)

        shortcuts = [
            ("toggle_spotlight", "Spotlight"), ("draw_blue", "Blue"),
            ("draw_red", "Red"), ("draw_yellow", "Yellow"),
            ("draw_green", "Green"), ("clear_screen", "Clear"), ("quit", "Quit")
        ]

        for i, (action, label) in enumerate(shortcuts):
            row, col = divmod(i, 2)
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
            lbl.setFixedWidth(55)
            recorder = ShortcutRecorder()
            self.shortcut_inputs[action] = recorder
            h = QHBoxLayout()
            h.setSpacing(4)
            h.addWidget(lbl)
            h.addWidget(recorder, 1)
            grid.addLayout(h, row, col)

        layout.addLayout(grid)
        return widget

    def _create_spotlight_section(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        layout.addWidget(self._create_section_label("SPOTLIGHT"))

        # Sliders in compact rows
        for name, attr, min_v, max_v, suffix in [
            ("Radius", "radius_slider", 5, 200, "px"),
            ("Ring", "ring_radius_slider", 5, 100, "px"),
            ("Opacity", "opacity_slider", 0, 100, "%"),
        ]:
            row = QHBoxLayout()
            row.setSpacing(6)
            lbl = QLabel(name)
            lbl.setFixedWidth(45)
            lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
            slider = NoScrollSlider(Qt.Horizontal)
            slider.setMinimum(min_v)
            slider.setMaximum(max_v)
            slider.setFixedHeight(16)
            slider.setStyleSheet(f"""
                QSlider::groove:horizontal {{
                    height: 3px;
                    background: {COLORS['surface_elevated']};
                    border-radius: 1px;
                }}
                QSlider::handle:horizontal {{
                    background: {COLORS['text_secondary']};
                    width: 10px;
                    height: 10px;
                    margin: -4px 0;
                    border-radius: 5px;
                }}
                QSlider::handle:horizontal:hover {{
                    background: {COLORS['text']};
                }}
                QSlider::sub-page:horizontal {{
                    background: {COLORS['accent_muted']};
                    border-radius: 1px;
                }}
            """)
            val_lbl = QLabel()
            val_lbl.setFixedWidth(35)
            val_lbl.setAlignment(Qt.AlignRight)
            val_lbl.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px;")
            setattr(self, attr, slider)
            setattr(self, attr.replace("slider", "label"), val_lbl)
            slider.valueChanged.connect(lambda v, l=val_lbl, s=suffix: l.setText(f"{v}{s}"))
            slider.valueChanged.connect(self._update_live_preview)
            row.addWidget(lbl)
            row.addWidget(slider, 1)
            row.addWidget(val_lbl)
            layout.addLayout(row)

        # Color section
        color_row = QHBoxLayout()
        color_row.setSpacing(6)
        clbl = QLabel("Color")
        clbl.setFixedWidth(45)
        clbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        color_row.addWidget(clbl)

        # Preset colors - all on one line
        for color_hex in PRESET_COLORS:
            btn = ColorPresetButton(color_hex)
            btn.color_selected.connect(self._on_preset_color_selected)
            self.preset_buttons.append(btn)
            color_row.addWidget(btn)

        color_row.addStretch()
        layout.addLayout(color_row)

        # Color wheel row
        wheel_row = QHBoxLayout()
        wheel_row.setSpacing(8)

        self.color_wheel = ColorWheel()
        self.color_wheel.color_changed.connect(self._on_wheel_color_changed)
        wheel_row.addWidget(self.color_wheel)

        # Preview
        preview_col = QVBoxLayout()
        preview_col.setSpacing(4)
        self.spotlight_color_preview = QLabel()
        self.spotlight_color_preview.setFixedSize(50, 50)
        self.spotlight_color_preview.setStyleSheet(f"border: 1px solid {COLORS['border']}; border-radius: 4px;")
        preview_col.addWidget(self.spotlight_color_preview)
        preview_col.addStretch()
        wheel_row.addLayout(preview_col)
        wheel_row.addStretch()

        layout.addLayout(wheel_row)
        return widget

    def _create_drawing_section(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(self._create_section_label("DRAWING"))

        row = QHBoxLayout()
        row.setSpacing(6)
        lbl = QLabel("Width")
        lbl.setFixedWidth(45)
        lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        self.line_width_slider = NoScrollSlider(Qt.Horizontal)
        self.line_width_slider.setMinimum(1)
        self.line_width_slider.setMaximum(20)
        self.line_width_slider.setFixedHeight(16)
        self.line_width_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                height: 3px;
                background: {COLORS['surface_elevated']};
                border-radius: 1px;
            }}
            QSlider::handle:horizontal {{
                background: {COLORS['text_secondary']};
                width: 10px;
                height: 10px;
                margin: -4px 0;
                border-radius: 5px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {COLORS['text']};
            }}
            QSlider::sub-page:horizontal {{
                background: {COLORS['accent_muted']};
                border-radius: 1px;
            }}
        """)
        self.line_width_label = QLabel()
        self.line_width_label.setFixedWidth(35)
        self.line_width_label.setAlignment(Qt.AlignRight)
        self.line_width_label.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px;")
        self.line_width_slider.valueChanged.connect(lambda v: self.line_width_label.setText(f"{v}px"))
        row.addWidget(lbl)
        row.addWidget(self.line_width_slider, 1)
        row.addWidget(self.line_width_label)
        layout.addLayout(row)
        return widget

    def _create_tool_shortcuts_section(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        layout.addWidget(self._create_section_label("TOOL SHORTCUTS"))

        # Horizontal layout with tool name above input
        tools_row = QHBoxLayout()
        tools_row.setSpacing(8)

        tools = [("freehand", "Free"), ("line", "Line"), ("rectangle", "Rect"), ("arrow", "Arrow"), ("circle", "Circle")]
        self.tool_shortcut_inputs = {}

        for tool, label in tools:
            col = QVBoxLayout()
            col.setSpacing(2)
            lbl = QLabel(label)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 10px;")
            inp = QLineEdit()
            inp.setMaxLength(1)
            inp.setFixedSize(32, 22)
            inp.setAlignment(Qt.AlignCenter)
            inp.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {COLORS['surface']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 3px;
                    color: {COLORS['text']};
                    font-size: 11px;
                }}
                QLineEdit:focus {{
                    border-color: {COLORS['accent']};
                }}
            """)
            self.tool_shortcut_inputs[tool] = inp
            col.addWidget(lbl)
            col.addWidget(inp)
            tools_row.addLayout(col)

        tools_row.addStretch()
        layout.addLayout(tools_row)
        return widget

    def _create_button_bar(self):
        bar = QWidget()
        bar.setFixedHeight(40)
        bar.setStyleSheet(f"background-color: {COLORS['surface']}; border-top: 1px solid {COLORS['border']};")
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.addStretch()

        for text, callback, primary in [("Cancel", self.reject, False), ("Save", self._save_settings, True)]:
            btn = QPushButton(text)
            btn.setCursor(Qt.PointingHandCursor)
            if primary:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {COLORS['accent_muted']};
                        border: 1px solid {COLORS['border_focus']};
                        border-radius: 3px;
                        padding: 5px 16px;
                        color: {COLORS['accent']};
                        font-size: 11px;
                    }}
                    QPushButton:hover {{
                        background-color: {COLORS['border_focus']};
                    }}
                """)
            else:
                btn.setStyleSheet(f"""
                    QPushButton {{
                        background: transparent;
                        border: 1px solid {COLORS['border']};
                        border-radius: 3px;
                        padding: 5px 14px;
                        color: {COLORS['text_secondary']};
                        font-size: 11px;
                    }}
                    QPushButton:hover {{
                        background-color: {COLORS['surface_elevated']};
                        color: {COLORS['text']};
                    }}
                """)
            btn.clicked.connect(callback)
            layout.addWidget(btn)

        return bar

    def _load_settings(self):
        for slider in [self.radius_slider, self.ring_radius_slider, self.opacity_slider, self.line_width_slider]:
            slider.blockSignals(True)

        for action, recorder in self.shortcut_inputs.items():
            recorder.setText(self.config.get_shortcut(action))

        r = self.config.get("spotlight", "radius") or 80
        self.radius_slider.setValue(int(r))
        self.radius_label.setText(f"{int(r)}px")

        rr = self.config.get("spotlight", "ring_radius") or 40
        self.ring_radius_slider.setValue(int(rr))
        self.ring_radius_label.setText(f"{int(rr)}px")

        o = self.config.get("spotlight", "opacity") or 0.7
        self.opacity_slider.setValue(int(o * 100))
        self.opacity_label.setText(f"{int(o * 100)}%")

        self.spotlight_color = self.config.get("spotlight", "color") or "#FFFF64"
        self._update_color_ui()

        lw = self.config.get("drawing", "line_width") or 4
        self.line_width_slider.setValue(int(lw))
        self.line_width_label.setText(f"{int(lw)}px")

        ts = self.config.get("drawing", "tool_shortcuts") or {}
        defaults = {"freehand": "1", "line": "2", "rectangle": "3", "arrow": "4", "circle": "5"}
        for tool, inp in self.tool_shortcut_inputs.items():
            inp.setText(ts.get(tool, defaults.get(tool, "")))

        for slider in [self.radius_slider, self.ring_radius_slider, self.opacity_slider, self.line_width_slider]:
            slider.blockSignals(False)

    def _save_settings(self):
        for action, recorder in self.shortcut_inputs.items():
            if recorder.text():
                self.config.set_shortcut(action, recorder.text())

        self.config.set(self.radius_slider.value(), "spotlight", "radius")
        self.config.set(self.ring_radius_slider.value(), "spotlight", "ring_radius")
        self.config.set(self.opacity_slider.value() / 100.0, "spotlight", "opacity")
        self.config.set(self.spotlight_color, "spotlight", "color")
        self.config.set(self.line_width_slider.value(), "drawing", "line_width")

        for tool, inp in self.tool_shortcut_inputs.items():
            if inp.text().strip():
                self.config.set(inp.text().strip(), "drawing", "tool_shortcuts", tool)

        self.settings_changed.emit()
        self.accept()

    def _on_preset_color_selected(self, color_hex: str):
        self.spotlight_color = color_hex
        self._update_color_ui()
        self._update_live_preview()

    def _on_wheel_color_changed(self, color_hex: str):
        self.spotlight_color = color_hex
        self._update_color_ui(update_wheel=False)
        self._update_live_preview()

    def _update_color_ui(self, update_wheel=True):
        self.spotlight_color_preview.setStyleSheet(f"background-color: {self.spotlight_color}; border: 1px solid {COLORS['border']}; border-radius: 4px;")
        for btn in self.preset_buttons:
            btn.set_selected(btn.color_hex.upper() == self.spotlight_color.upper())
        if update_wheel:
            self.color_wheel.set_color(self.spotlight_color)

    def _update_live_preview(self):
        if self.overlay:
            self.config.set(self.radius_slider.value(), "spotlight", "radius")
            self.config.set(self.ring_radius_slider.value(), "spotlight", "ring_radius")
            self.config.set(self.opacity_slider.value() / 100.0, "spotlight", "opacity")
            self.config.set(self.spotlight_color, "spotlight", "color")
            self.overlay.update()

    # Draggable window
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and event.pos().y() < 32:
            self._drag_pos = event.globalPos() - self.pos()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None
