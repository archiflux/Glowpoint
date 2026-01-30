"""Settings dialog for configuring shortcuts and preferences."""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QGroupBox, QFormLayout,
                             QSlider, QColorDialog, QFrame, QWidget,
                             QScrollArea, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor, QFont


# Sophisticated OLED-optimized dark theme
# True blacks for OLED efficiency, soft whites for reduced eye strain
COLORS = {
    "background": "#000000",        # True black for OLED
    "surface": "#0d0d0d",           # Near-black surface
    "surface_elevated": "#161616",  # Slightly elevated surface
    "surface_hover": "#1f1f1f",     # Hover state
    "text": "#d4d4d4",              # Soft white - not pure white
    "text_secondary": "#858585",    # Muted secondary text
    "text_dim": "#525252",          # Dimmed text for tertiary info
    "accent": "#4a9eff",            # Soft blue accent - easy on eyes
    "accent_hover": "#6bb3ff",      # Lighter accent for hover
    "accent_muted": "#1a3a5c",      # Very muted accent for backgrounds
    "border": "#1f1f1f",            # Subtle border
    "border_focus": "#2d4a6a",      # Focus border - muted accent
    "success": "#3d8c40",           # Muted green
    "error": "#c45c5c",             # Muted red
}

# Preset spotlight colors - bright but with slight softening
PRESET_COLORS = [
    ("#FFEE58", "Yellow"),      # Soft yellow
    ("#66BB6A", "Green"),       # Soft green
    ("#4DD0E1", "Cyan"),        # Soft cyan
    ("#BA68C8", "Purple"),      # Soft purple
    ("#FF8A65", "Orange"),      # Soft orange
    ("#F06292", "Pink"),        # Soft pink
    ("#81C784", "Mint"),        # Soft mint
    ("#7986CB", "Indigo"),      # Soft indigo
]


class ShortcutRecorder(QLineEdit):
    """Widget for recording keyboard shortcuts."""

    def __init__(self, parent=None):
        """Initialize shortcut recorder."""
        super().__init__(parent)
        self.setReadOnly(True)
        self.setPlaceholderText("Click to record...")
        self.recording = False
        self.keys = []
        self._apply_style()

    def _apply_style(self):
        """Apply OLED-optimized styling."""
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 8px 12px;
                color: {COLORS['text']};
                font-size: 13px;
                selection-background-color: {COLORS['accent_muted']};
            }}
            QLineEdit:hover {{
                background-color: {COLORS['surface_elevated']};
                border-color: {COLORS['border_focus']};
            }}
            QLineEdit:focus {{
                border-color: {COLORS['accent']};
            }}
        """)

    def mousePressEvent(self, event):
        """Start recording when clicked."""
        super().mousePressEvent(event)
        if not self.recording:
            self.recording = True
            self.keys = []
            self.setText("")
            self.setStyleSheet(f"""
                QLineEdit {{
                    background-color: {COLORS['surface_elevated']};
                    border: 1px solid {COLORS['accent']};
                    border-radius: 4px;
                    padding: 8px 12px;
                    color: {COLORS['accent']};
                    font-size: 13px;
                }}
            """)

    def focusOutEvent(self, event):
        """Stop recording when focus is lost."""
        super().focusOutEvent(event)
        self.recording = False
        self._apply_style()

    def keyPressEvent(self, event):
        """Record key press."""
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
                Qt.Key_Escape: "esc",
                Qt.Key_Tab: "tab",
                Qt.Key_Space: "space",
                Qt.Key_Return: "enter",
                Qt.Key_Enter: "enter",
            }.get(key)
            if key_name:
                key_text = f"<{key_name}>"

        if key_text:
            parts.append(key_text)

        if len(parts) >= 2:
            shortcut = "+".join(parts)
            self.setText(shortcut)
            self.recording = False
            self._apply_style()
        elif len(parts) == 1 and not parts[0].startswith("<"):
            self.setText(parts[0])
            self.recording = False
            self._apply_style()


class ColorPresetButton(QPushButton):
    """A clickable color preset button."""

    color_selected = pyqtSignal(str)

    def __init__(self, color_hex: str, color_name: str, parent=None):
        super().__init__(parent)
        self.color_hex = color_hex
        self.color_name = color_name
        self.setFixedSize(28, 28)
        self.setToolTip(color_name)
        self.setCursor(Qt.PointingHandCursor)
        self._update_style(selected=False)
        self.clicked.connect(self._on_click)

    def _update_style(self, selected: bool = False):
        """Update button style with subtle depth."""
        if selected:
            border = f"2px solid {COLORS['accent']}"
            shadow = f"0 0 8px {self.color_hex}"
        else:
            border = f"1px solid {COLORS['border']}"
            shadow = "none"
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.color_hex};
                border: {border};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border: 1px solid {COLORS['text_secondary']};
            }}
        """)

    def _on_click(self):
        self.color_selected.emit(self.color_hex)

    def set_selected(self, selected: bool):
        self._update_style(selected)


class SettingsDialog(QDialog):
    """Dialog for configuring application settings."""

    settings_changed = pyqtSignal()

    def __init__(self, config_manager, overlay=None, parent=None):
        """Initialize settings dialog."""
        super().__init__(parent)
        self.config = config_manager
        self.overlay = overlay
        self.shortcut_inputs = {}
        self.spotlight_color = "#FFFF64"
        self.preset_buttons = []
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("Settings")
        self.setMinimumWidth(480)
        self.setMinimumHeight(580)

        # Apply OLED-optimized styling
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {COLORS['background']};
            }}
            QGroupBox {{
                font-size: 13px;
                font-weight: 500;
                color: {COLORS['text_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                margin-top: 16px;
                padding: 12px 12px 12px 12px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: {COLORS['text_secondary']};
            }}
            QLabel {{
                color: {COLORS['text']};
                font-size: 13px;
            }}
            QSlider::groove:horizontal {{
                border: none;
                height: 4px;
                background: {COLORS['surface_elevated']};
                border-radius: 2px;
            }}
            QSlider::handle:horizontal {{
                background: {COLORS['text_secondary']};
                border: none;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }}
            QSlider::handle:horizontal:hover {{
                background: {COLORS['text']};
            }}
            QSlider::sub-page:horizontal {{
                background: {COLORS['accent_muted']};
                border-radius: 2px;
            }}
            QLineEdit {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 8px 12px;
                color: {COLORS['text']};
                font-size: 13px;
            }}
            QLineEdit:hover {{
                background-color: {COLORS['surface_elevated']};
            }}
            QLineEdit:focus {{
                border-color: {COLORS['accent']};
            }}
        """)

        # Main layout with scroll area
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

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
                width: 6px;
                border-radius: 3px;
                margin: 4px 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {COLORS['surface_elevated']};
                border-radius: 3px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {COLORS['text_dim']};
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0;
            }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
                background: none;
            }}
        """)

        content_widget = QWidget()
        content_widget.setStyleSheet(f"background-color: {COLORS['background']};")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 16, 20, 16)
        content_layout.setSpacing(12)

        # Title
        title_label = QLabel("Settings")
        title_label.setStyleSheet(f"""
            font-size: 20px;
            font-weight: 600;
            color: {COLORS['text']};
            padding-bottom: 4px;
        """)
        content_layout.addWidget(title_label)

        # Keyboard Shortcuts section
        shortcuts_group = self._create_shortcuts_section()
        content_layout.addWidget(shortcuts_group)

        # Spotlight Settings section
        spotlight_group = self._create_spotlight_section()
        content_layout.addWidget(spotlight_group)

        # Drawing Settings section
        drawing_group = self._create_drawing_section()
        content_layout.addWidget(drawing_group)

        # Tool Shortcuts section
        tools_group = self._create_tool_shortcuts_section()
        content_layout.addWidget(tools_group)

        content_layout.addStretch()
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        # Button bar at bottom
        button_bar = self._create_button_bar()
        main_layout.addWidget(button_bar)

    def _create_shortcuts_section(self):
        """Create keyboard shortcuts section."""
        group = QGroupBox("Keyboard Shortcuts")
        layout = QFormLayout(group)
        layout.setContentsMargins(12, 20, 12, 12)
        layout.setSpacing(10)
        layout.setLabelAlignment(Qt.AlignRight)

        shortcut_labels = {
            "toggle_spotlight": "Spotlight",
            "draw_blue": "Draw Blue",
            "draw_red": "Draw Red",
            "draw_yellow": "Draw Yellow",
            "draw_green": "Draw Green",
            "clear_screen": "Clear",
            "quit": "Quit"
        }

        for action, label in shortcut_labels.items():
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
            recorder = ShortcutRecorder()
            self.shortcut_inputs[action] = recorder
            layout.addRow(lbl, recorder)

        return group

    def _create_spotlight_section(self):
        """Create spotlight settings section."""
        group = QGroupBox("Spotlight")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 20, 12, 12)
        layout.setSpacing(14)

        # Radius slider
        radius_layout = self._create_slider_row("Radius", 5, 200)
        self.radius_slider = radius_layout.itemAt(1).widget()
        self.radius_label = radius_layout.itemAt(2).widget()
        self.radius_slider.valueChanged.connect(self._on_radius_changed)
        layout.addLayout(radius_layout)

        # Ring radius slider
        ring_layout = self._create_slider_row("Ring", 5, 100)
        self.ring_radius_slider = ring_layout.itemAt(1).widget()
        self.ring_radius_label = ring_layout.itemAt(2).widget()
        self.ring_radius_slider.valueChanged.connect(self._on_ring_radius_changed)
        layout.addLayout(ring_layout)

        # Opacity slider
        opacity_layout = self._create_slider_row("Opacity", 0, 100)
        self.opacity_slider = opacity_layout.itemAt(1).widget()
        self.opacity_label = opacity_layout.itemAt(2).widget()
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        layout.addLayout(opacity_layout)

        # Color section
        color_label = QLabel("Color")
        color_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 13px;")
        layout.addWidget(color_label)

        # Preset colors row
        preset_layout = QHBoxLayout()
        preset_layout.setSpacing(6)
        for color_hex, color_name in PRESET_COLORS:
            btn = ColorPresetButton(color_hex, color_name)
            btn.color_selected.connect(self._on_preset_color_selected)
            self.preset_buttons.append(btn)
            preset_layout.addWidget(btn)
        preset_layout.addStretch()
        layout.addLayout(preset_layout)

        # Custom color picker row
        color_picker_layout = QHBoxLayout()
        color_picker_layout.setSpacing(10)

        self.spotlight_color_preview = QLabel()
        self.spotlight_color_preview.setFixedSize(32, 32)
        self.spotlight_color_preview.setStyleSheet(f"""
            border: 1px solid {COLORS['border']};
            border-radius: 4px;
        """)
        color_picker_layout.addWidget(self.spotlight_color_preview)

        self.spotlight_color_button = QPushButton("Custom...")
        self.spotlight_color_button.setCursor(Qt.PointingHandCursor)
        self.spotlight_color_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 8px 16px;
                color: {COLORS['text_secondary']};
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['surface_elevated']};
                color: {COLORS['text']};
            }}
        """)
        self.spotlight_color_button.clicked.connect(self._choose_spotlight_color)
        color_picker_layout.addWidget(self.spotlight_color_button)
        color_picker_layout.addStretch()

        layout.addLayout(color_picker_layout)

        return group

    def _create_drawing_section(self):
        """Create drawing settings section."""
        group = QGroupBox("Drawing")
        layout = QVBoxLayout(group)
        layout.setContentsMargins(12, 20, 12, 12)
        layout.setSpacing(14)

        # Line width slider
        line_layout = self._create_slider_row("Line Width", 1, 20)
        self.line_width_slider = line_layout.itemAt(1).widget()
        self.line_width_label = line_layout.itemAt(2).widget()
        self.line_width_slider.valueChanged.connect(
            lambda v: self.line_width_label.setText(f"{v}px")
        )
        layout.addLayout(line_layout)

        return group

    def _create_tool_shortcuts_section(self):
        """Create tool shortcuts section."""
        group = QGroupBox("Tool Shortcuts")
        layout = QFormLayout(group)
        layout.setContentsMargins(12, 20, 12, 12)
        layout.setSpacing(10)
        layout.setLabelAlignment(Qt.AlignRight)

        tool_labels = {
            "freehand": "Freehand",
            "line": "Line",
            "rectangle": "Rectangle",
            "arrow": "Arrow",
            "circle": "Circle"
        }

        self.tool_shortcut_inputs = {}
        for tool, label in tool_labels.items():
            lbl = QLabel(label)
            lbl.setStyleSheet(f"color: {COLORS['text_secondary']};")
            input_field = QLineEdit()
            input_field.setMaxLength(1)
            input_field.setFixedWidth(44)
            input_field.setAlignment(Qt.AlignCenter)
            input_field.setPlaceholderText("—")
            self.tool_shortcut_inputs[tool] = input_field
            layout.addRow(lbl, input_field)

        return group

    def _create_slider_row(self, label_text, min_val, max_val):
        """Create a row with label, slider, and value display."""
        layout = QHBoxLayout()
        layout.setSpacing(12)

        label = QLabel(label_text)
        label.setFixedWidth(70)
        label.setStyleSheet(f"color: {COLORS['text_secondary']};")
        layout.addWidget(label)

        slider = QSlider(Qt.Horizontal)
        slider.setMinimum(min_val)
        slider.setMaximum(max_val)
        slider.setTickPosition(QSlider.NoTicks)
        layout.addWidget(slider, 1)

        value_label = QLabel()
        value_label.setFixedWidth(44)
        value_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        value_label.setStyleSheet(f"color: {COLORS['text_dim']};")
        layout.addWidget(value_label)

        return layout

    def _create_button_bar(self):
        """Create the bottom button bar."""
        bar = QWidget()
        bar.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['surface']};
                border-top: 1px solid {COLORS['border']};
            }}
        """)
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 12, 16, 12)

        layout.addStretch()

        cancel_button = QPushButton("Cancel")
        cancel_button.setCursor(Qt.PointingHandCursor)
        cancel_button.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                padding: 8px 20px;
                color: {COLORS['text_secondary']};
                font-size: 13px;
            }}
            QPushButton:hover {{
                background-color: {COLORS['surface_elevated']};
                color: {COLORS['text']};
            }}
        """)
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(cancel_button)

        save_button = QPushButton("Save")
        save_button.setCursor(Qt.PointingHandCursor)
        save_button.setStyleSheet(f"""
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
        save_button.clicked.connect(self._save_settings)
        layout.addWidget(save_button)

        return bar

    def _load_settings(self):
        """Load current settings into the dialog."""
        self.radius_slider.blockSignals(True)
        self.ring_radius_slider.blockSignals(True)
        self.opacity_slider.blockSignals(True)
        self.line_width_slider.blockSignals(True)

        try:
            # Load shortcuts
            for action, recorder in self.shortcut_inputs.items():
                shortcut = self.config.get_shortcut(action)
                recorder.setText(shortcut)

            # Load spotlight settings
            radius = self.config.get("spotlight", "radius")
            if radius is None or not isinstance(radius, (int, float)):
                radius = 80
            self.radius_slider.setValue(int(radius))
            self.radius_label.setText(f"{int(radius)}px")

            ring_radius = self.config.get("spotlight", "ring_radius")
            if ring_radius is None or not isinstance(ring_radius, (int, float)):
                ring_radius = 40
            self.ring_radius_slider.setValue(int(ring_radius))
            self.ring_radius_label.setText(f"{int(ring_radius)}px")

            opacity = self.config.get("spotlight", "opacity")
            if opacity is None or not isinstance(opacity, (int, float)):
                opacity = 0.7
            opacity_percent = int(opacity * 100)
            self.opacity_slider.setValue(opacity_percent)
            self.opacity_label.setText(f"{opacity_percent}%")

            self.spotlight_color = self.config.get("spotlight", "color") or "#FFFF64"
            self._update_color_preview()
            self._update_preset_selection()

            # Load drawing settings
            line_width = self.config.get("drawing", "line_width")
            if line_width is None or not isinstance(line_width, (int, float)):
                line_width = 4
            self.line_width_slider.setValue(int(line_width))
            self.line_width_label.setText(f"{int(line_width)}px")

            # Load tool shortcuts
            tool_shortcuts = self.config.get("drawing", "tool_shortcuts") or {}
            default_shortcuts = {"freehand": "1", "line": "2", "rectangle": "3", "arrow": "4", "circle": "5"}
            for tool, input_field in self.tool_shortcut_inputs.items():
                shortcut = tool_shortcuts.get(tool, default_shortcuts.get(tool, ""))
                input_field.setText(shortcut)
        finally:
            self.radius_slider.blockSignals(False)
            self.ring_radius_slider.blockSignals(False)
            self.opacity_slider.blockSignals(False)
            self.line_width_slider.blockSignals(False)

    def _save_settings(self):
        """Save settings to configuration silently."""
        # Save shortcuts
        for action, recorder in self.shortcut_inputs.items():
            shortcut = recorder.text()
            if shortcut:
                self.config.set_shortcut(action, shortcut)

        # Save spotlight settings
        self.config.set(self.radius_slider.value(), "spotlight", "radius")
        self.config.set(self.ring_radius_slider.value(), "spotlight", "ring_radius")
        self.config.set(self.opacity_slider.value() / 100.0, "spotlight", "opacity")
        self.config.set(self.spotlight_color, "spotlight", "color")

        # Save drawing settings
        self.config.set(self.line_width_slider.value(), "drawing", "line_width")

        # Save tool shortcuts
        for tool, input_field in self.tool_shortcut_inputs.items():
            shortcut = input_field.text().strip()
            if shortcut:
                self.config.set(shortcut, "drawing", "tool_shortcuts", tool)

        self.settings_changed.emit()
        self.accept()

    def _on_preset_color_selected(self, color_hex: str):
        """Handle preset color selection."""
        self.spotlight_color = color_hex
        self._update_color_preview()
        self._update_preset_selection()
        self._update_live_preview()

    def _update_preset_selection(self):
        """Update which preset button is selected."""
        for btn in self.preset_buttons:
            btn.set_selected(btn.color_hex.upper() == self.spotlight_color.upper())

    def _choose_spotlight_color(self):
        """Open color picker for custom spotlight color."""
        current_color = QColor(self.spotlight_color)
        color = QColorDialog.getColor(current_color, self, "Choose Spotlight Color")
        if color.isValid():
            self.spotlight_color = color.name()
            self._update_color_preview()
            self._update_preset_selection()
            self._update_live_preview()

    def _update_color_preview(self):
        """Update the color preview box."""
        self.spotlight_color_preview.setStyleSheet(f"""
            background-color: {self.spotlight_color};
            border: 1px solid {COLORS['border']};
            border-radius: 4px;
        """)

    def _on_radius_changed(self, value):
        """Handle spotlight radius changes."""
        self.radius_label.setText(f"{value}px")
        self._update_live_preview()

    def _on_ring_radius_changed(self, value):
        """Handle ring radius changes."""
        self.ring_radius_label.setText(f"{value}px")
        self._update_live_preview()

    def _on_opacity_changed(self, value):
        """Handle opacity changes."""
        self.opacity_label.setText(f"{value}%")
        self._update_live_preview()

    def _update_live_preview(self):
        """Update the overlay with current settings for live preview."""
        if self.overlay:
            self.config.set(self.radius_slider.value(), "spotlight", "radius")
            self.config.set(self.ring_radius_slider.value(), "spotlight", "ring_radius")
            self.config.set(self.opacity_slider.value() / 100.0, "spotlight", "opacity")
            self.config.set(self.spotlight_color, "spotlight", "color")
            self.overlay.update()
