"""Global hotkey manager using pynput."""
from pynput import keyboard
from typing import Callable, Dict
from PyQt5.QtCore import QObject, pyqtSignal


class HotkeyManager(QObject):
    """Manages global keyboard shortcuts."""

    # Signals for hotkey events
    spotlight_toggle = pyqtSignal()
    draw_blue = pyqtSignal()
    draw_red = pyqtSignal()
    draw_yellow = pyqtSignal()
    draw_green = pyqtSignal()
    clear_screen = pyqtSignal()
    quit_app = pyqtSignal()

    def __init__(self, config_manager):
        """Initialize hotkey manager.

        Args:
            config_manager: Configuration manager instance
        """
        super().__init__()
        self.config = config_manager
        self.listener = None
        self._setup_hotkeys()

    def _convert_shortcut(self, shortcut: str) -> str:
        """Convert shortcut string to pynput format.

        Args:
            shortcut: Shortcut string like "<ctrl>+<shift>+s"

        Returns:
            Pynput format string like "<ctrl>+<shift>+s"
        """
        # pynput's GlobalHotKeys uses the same format, just ensure consistency
        return shortcut.lower().replace(" ", "")

    def _setup_hotkeys(self):
        """Set up hotkey mappings from configuration."""
        # Build hotkey dictionary for GlobalHotKeys
        hotkeys = {}

        # Create wrapper functions to ensure proper signal emission
        def make_callback(signal):
            """Create a callback that emits the signal.

            Args:
                signal: PyQt signal to emit

            Returns:
                Callback function
            """
            def callback():
                print(f"Hotkey triggered! Emitting signal: {signal}")
                signal.emit()
            return callback

        actions = {
            "toggle_spotlight": self.spotlight_toggle,
            "draw_blue": self.draw_blue,
            "draw_red": self.draw_red,
            "draw_yellow": self.draw_yellow,
            "draw_green": self.draw_green,
            "clear_screen": self.clear_screen,
            "quit": self.quit_app,
        }

        for action, signal in actions.items():
            shortcut = self.config.get_shortcut(action)
            if shortcut:
                hotkey_str = self._convert_shortcut(shortcut)
                hotkeys[hotkey_str] = make_callback(signal)
                print(f"Registered hotkey: {hotkey_str} for {action}")

        self.hotkeys = hotkeys
        print(f"Total hotkeys registered: {len(self.hotkeys)}")

    def start(self):
        """Start listening for global hotkeys."""
        if self.listener is None:
            try:
                self.listener = keyboard.GlobalHotKeys(self.hotkeys)
                self.listener.start()
                print("Hotkey listener started successfully")
            except Exception as e:
                print(f"Error starting hotkey listener: {e}")
                print("Registered hotkeys:", list(self.hotkeys.keys()))

    def stop(self):
        """Stop listening for global hotkeys."""
        if self.listener is not None:
            self.listener.stop()
            self.listener = None

    def reload_hotkeys(self):
        """Reload hotkeys from configuration."""
        self.stop()
        self._setup_hotkeys()
        self.start()
