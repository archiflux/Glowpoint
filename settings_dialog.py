"""Settings dialog for configuring shortcuts and preferences."""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QGroupBox, QFormLayout,
                             QSlider, QCheckBox, QMessageBox, QColorDialog)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QColor


class ShortcutRecorder(QLineEdit):
    """Widget for recording keyboard shortcuts."""

    def __init__(self, parent=None):
        """Initialize shortcut recorder."""
        super().__init__(parent)
        self.setReadOnly(True)
        self.setPlaceholderText("Click and press your shortcut...")
        self.recording = False
        self.keys = []

    def mousePressEvent(self, event):
        """Start recording when clicked."""
        super().mousePressEvent(event)
        if not self.recording:
            self.recording = True
            self.keys = []
            self.setText("")
            self.setStyleSheet("background-color: #FFF9C4;")

    def focusInEvent(self, event):
        """Handle focus - don't auto-start recording."""
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        """Stop recording when focus is lost."""
        super().focusOutEvent(event)
        self.recording = False
        self.setStyleSheet("")

    def keyPressEvent(self, event):
        """Record key press."""
        if not self.recording:
            return

        key = event.key()
        modifiers = event.modifiers()

        # Ignore pure modifier keys
        if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
            return

        # Build shortcut string
        parts = []
        if modifiers & Qt.ControlModifier:
            parts.append("<ctrl>")
        if modifiers & Qt.ShiftModifier:
            parts.append("<shift>")
        if modifiers & Qt.AltModifier:
            parts.append("<alt>")
        if modifiers & Qt.MetaModifier:
            parts.append("<cmd>")

        # Add main key
        key_text = event.text().lower()
        if key_text and key_text.isprintable():
            parts.append(key_text)
        else:
            # Special keys
            key_name = {
                Qt.Key_Escape: "esc",
                Qt.Key_Tab: "tab",
                Qt.Key_Space: "space",
                Qt.Key_Return: "enter",
                Qt.Key_Enter: "enter",
            }.get(key)
            if key_name:
                parts.append(f"<{key_name}>")

        # Set the shortcut if we have at least one modifier and one key
        if len(parts) >= 2:
            shortcut = "+".join(parts)
            self.setText(shortcut)
            self.recording = False
            self.setStyleSheet("")
        elif len(parts) == 1 and not parts[0].startswith("<"):
            # Single key without modifier - also accept it
            self.setText(parts[0])
            self.recording = False
            self.setStyleSheet("")


class SettingsDialog(QDialog):
    """Dialog for configuring application settings."""

    settings_changed = pyqtSignal()

    def __init__(self, config_manager, overlay=None, parent=None):
        """Initialize settings dialog.

        Args:
            config_manager: Configuration manager instance
            overlay: Overlay window for live preview
            parent: Parent widget
        """
        super().__init__(parent)
        self.config = config_manager
        self.overlay = overlay
        self.shortcut_inputs = {}
        self.spotlight_color = "#FFFF64"  # Default yellow
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("Glowpoint Settings")
        self.setMinimumWidth(500)

        layout = QVBoxLayout()

        # Shortcuts section
        shortcuts_group = QGroupBox("Keyboard Shortcuts")
        shortcuts_layout = QFormLayout()

        shortcut_labels = {
            "toggle_spotlight": "Toggle Spotlight",
            "draw_blue": "Draw Blue",
            "draw_red": "Draw Red",
            "draw_yellow": "Draw Yellow",
            "draw_green": "Draw Green",
            "clear_screen": "Clear Screen",
            "quit": "Quit Application"
        }

        for action, label in shortcut_labels.items():
            recorder = ShortcutRecorder()
            self.shortcut_inputs[action] = recorder
            shortcuts_layout.addRow(label + ":", recorder)

        shortcuts_group.setLayout(shortcuts_layout)
        layout.addWidget(shortcuts_group)

        # Spotlight settings section
        spotlight_group = QGroupBox("Spotlight Settings")
        spotlight_layout = QFormLayout()

        # Spotlight radius slider
        self.radius_slider = QSlider(Qt.Horizontal)
        self.radius_slider.setMinimum(50)
        self.radius_slider.setMaximum(200)
        self.radius_slider.setTickPosition(QSlider.TicksBelow)
        self.radius_slider.setTickInterval(25)
        self.radius_label = QLabel()
        radius_layout = QHBoxLayout()
        radius_layout.addWidget(self.radius_slider)
        radius_layout.addWidget(self.radius_label)
        self.radius_slider.valueChanged.connect(self._on_radius_changed)
        spotlight_layout.addRow("Spotlight Radius:", radius_layout)

        # Ring radius slider
        self.ring_radius_slider = QSlider(Qt.Horizontal)
        self.ring_radius_slider.setMinimum(10)
        self.ring_radius_slider.setMaximum(100)
        self.ring_radius_slider.setTickPosition(QSlider.TicksBelow)
        self.ring_radius_slider.setTickInterval(10)
        self.ring_radius_label = QLabel()
        ring_radius_layout = QHBoxLayout()
        ring_radius_layout.addWidget(self.ring_radius_slider)
        ring_radius_layout.addWidget(self.ring_radius_label)
        self.ring_radius_slider.valueChanged.connect(self._on_ring_radius_changed)
        spotlight_layout.addRow("Ring Radius:", ring_radius_layout)

        # Spotlight opacity slider
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setMinimum(0)
        self.opacity_slider.setMaximum(100)
        self.opacity_slider.setTickPosition(QSlider.TicksBelow)
        self.opacity_slider.setTickInterval(10)
        self.opacity_label = QLabel()
        opacity_layout = QHBoxLayout()
        opacity_layout.addWidget(self.opacity_slider)
        opacity_layout.addWidget(self.opacity_label)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        spotlight_layout.addRow("Glow Opacity:", opacity_layout)

        # Spotlight color picker
        self.spotlight_color_button = QPushButton("Choose Color")
        self.spotlight_color_button.clicked.connect(self._choose_spotlight_color)
        self.spotlight_color_preview = QLabel()
        self.spotlight_color_preview.setFixedSize(30, 30)
        self.spotlight_color_preview.setStyleSheet("border: 1px solid #ccc;")
        color_layout = QHBoxLayout()
        color_layout.addWidget(self.spotlight_color_button)
        color_layout.addWidget(self.spotlight_color_preview)
        color_layout.addStretch()
        spotlight_layout.addRow("Spotlight Color:", color_layout)

        spotlight_group.setLayout(spotlight_layout)
        layout.addWidget(spotlight_group)

        # Drawing settings section
        drawing_group = QGroupBox("Drawing Settings")
        drawing_layout = QFormLayout()

        # Line width slider
        self.line_width_slider = QSlider(Qt.Horizontal)
        self.line_width_slider.setMinimum(1)
        self.line_width_slider.setMaximum(20)
        self.line_width_slider.setTickPosition(QSlider.TicksBelow)
        self.line_width_slider.setTickInterval(2)
        self.line_width_label = QLabel()
        line_width_layout = QHBoxLayout()
        line_width_layout.addWidget(self.line_width_slider)
        line_width_layout.addWidget(self.line_width_label)
        self.line_width_slider.valueChanged.connect(
            lambda v: self.line_width_label.setText(f"{v}px")
        )
        drawing_layout.addRow("Line Width:", line_width_layout)

        drawing_group.setLayout(drawing_layout)
        layout.addWidget(drawing_group)

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        save_button.clicked.connect(self._save_settings)
        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _load_settings(self):
        """Load current settings into the dialog."""
        # Load shortcuts
        for action, recorder in self.shortcut_inputs.items():
            shortcut = self.config.get_shortcut(action)
            recorder.setText(shortcut)

        # Load spotlight settings
        radius = self.config.get("spotlight", "radius")
        self.radius_slider.setValue(radius)
        self.radius_label.setText(f"{radius}px")

        ring_radius = self.config.get("spotlight", "ring_radius")
        self.ring_radius_slider.setValue(ring_radius)
        self.ring_radius_label.setText(f"{ring_radius}px")

        opacity = int(self.config.get("spotlight", "opacity") * 100)
        self.opacity_slider.setValue(opacity)
        self.opacity_label.setText(f"{opacity}%")

        self.spotlight_color = self.config.get("spotlight", "color")
        self._update_color_preview()

        # Load drawing settings
        line_width = self.config.get("drawing", "line_width")
        self.line_width_slider.setValue(line_width)
        self.line_width_label.setText(f"{line_width}px")

    def _save_settings(self):
        """Save settings to configuration."""
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

        self.settings_changed.emit()
        QMessageBox.information(self, "Settings Saved",
                               "Settings have been saved successfully!\n\n"
                               "Note: Restart the application for shortcut changes to take effect.")
        self.accept()

    def _choose_spotlight_color(self):
        """Open color picker for spotlight color."""
        current_color = QColor(self.spotlight_color)
        color = QColorDialog.getColor(current_color, self, "Choose Spotlight Color")
        if color.isValid():
            self.spotlight_color = color.name()
            self._update_color_preview()
            self._update_live_preview()

    def _update_color_preview(self):
        """Update the color preview box."""
        self.spotlight_color_preview.setStyleSheet(
            f"background-color: {self.spotlight_color}; border: 1px solid #ccc;"
        )

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
            # Temporarily update config values for preview
            self.config.set(self.radius_slider.value(), "spotlight", "radius")
            self.config.set(self.ring_radius_slider.value(), "spotlight", "ring_radius")
            self.config.set(self.opacity_slider.value() / 100.0, "spotlight", "opacity")
            self.config.set(self.spotlight_color, "spotlight", "color")
            # Force overlay to repaint
            self.overlay.update()
