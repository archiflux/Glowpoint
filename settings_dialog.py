"""Settings dialog for configuring shortcuts and preferences."""
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QLineEdit, QGroupBox, QFormLayout,
                             QSlider, QCheckBox, QMessageBox)
from PyQt5.QtCore import Qt, pyqtSignal


class ShortcutRecorder(QLineEdit):
    """Widget for recording keyboard shortcuts."""

    def __init__(self, parent=None):
        """Initialize shortcut recorder."""
        super().__init__(parent)
        self.setReadOnly(True)
        self.setPlaceholderText("Click and press your shortcut...")
        self.recording = False
        self.keys = []

    def focusInEvent(self, event):
        """Start recording when focused."""
        super().focusInEvent(event)
        self.recording = True
        self.keys = []
        self.setText("")
        self.setStyleSheet("background-color: #FFF9C4;")

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
        if key not in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
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

        if len(parts) > 1:  # Need at least one modifier and one key
            shortcut = "+".join(parts)
            self.setText(shortcut)


class SettingsDialog(QDialog):
    """Dialog for configuring application settings."""

    settings_changed = pyqtSignal()

    def __init__(self, config_manager, parent=None):
        """Initialize settings dialog.

        Args:
            config_manager: Configuration manager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.config = config_manager
        self.shortcut_inputs = {}
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("SpotCursor Settings")
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
        self.radius_slider.valueChanged.connect(
            lambda v: self.radius_label.setText(f"{v}px")
        )
        spotlight_layout.addRow("Spotlight Radius:", radius_layout)

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
        self.opacity_slider.valueChanged.connect(
            lambda v: self.opacity_label.setText(f"{v}%")
        )
        spotlight_layout.addRow("Dimming Opacity:", opacity_layout)

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

        opacity = int(self.config.get("spotlight", "opacity") * 100)
        self.opacity_slider.setValue(opacity)

        # Load drawing settings
        line_width = self.config.get("drawing", "line_width")
        self.line_width_slider.setValue(line_width)

    def _save_settings(self):
        """Save settings to configuration."""
        # Save shortcuts
        for action, recorder in self.shortcut_inputs.items():
            shortcut = recorder.text()
            if shortcut:
                self.config.set_shortcut(action, shortcut)

        # Save spotlight settings
        self.config.set(self.radius_slider.value(), "spotlight", "radius")
        self.config.set(self.opacity_slider.value() / 100.0, "spotlight", "opacity")

        # Save drawing settings
        self.config.set(self.line_width_slider.value(), "drawing", "line_width")

        self.settings_changed.emit()
        QMessageBox.information(self, "Settings Saved",
                               "Settings have been saved successfully!\n\n"
                               "Note: Restart the application for shortcut changes to take effect.")
        self.accept()
