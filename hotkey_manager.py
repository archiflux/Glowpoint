"""Global hotkey manager using pynput."""
from pynput import keyboard
from typing import Callable, Dict, Set
from PyQt5.QtCore import QObject, pyqtSignal


class HotkeyManager(QObject):
    """Manages global keyboard shortcuts."""

    # Signals for hotkey events
    spotlight_toggle = pyqtSignal()
    draw_blue = pyqtSignal()
    draw_red = pyqtSignal()
    draw_yellow = pyqtSignal()
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
        self.current_keys: Set[keyboard.Key] = set()
        self.hotkey_actions: Dict[frozenset, Callable] = {}
        self._setup_hotkeys()

    def _parse_shortcut(self, shortcut: str) -> Set:
        """Parse shortcut string into set of keys.

        Args:
            shortcut: Shortcut string like "<ctrl>+<shift>+s"

        Returns:
            Set of keyboard keys
        """
        keys = set()
        parts = shortcut.lower().replace(" ", "").split("+")

        key_map = {
            "<ctrl>": keyboard.Key.ctrl_l,
            "<shift>": keyboard.Key.shift_l,
            "<alt>": keyboard.Key.alt_l,
            "<cmd>": keyboard.Key.cmd,
            "<super>": keyboard.Key.cmd,
        }

        for part in parts:
            if part in key_map:
                keys.add(key_map[part])
            elif len(part) == 1:
                # Single character key
                try:
                    keys.add(keyboard.KeyCode.from_char(part))
                except:
                    pass
            elif part.startswith("<") and part.endswith(">"):
                # Key name like <esc>, <tab>
                key_name = part[1:-1]
                try:
                    keys.add(getattr(keyboard.Key, key_name))
                except:
                    pass

        return keys

    def _setup_hotkeys(self):
        """Set up hotkey mappings from configuration."""
        shortcuts = {
            "toggle_spotlight": self.spotlight_toggle.emit,
            "draw_blue": self.draw_blue.emit,
            "draw_red": self.draw_red.emit,
            "draw_yellow": self.draw_yellow.emit,
            "clear_screen": self.clear_screen.emit,
            "quit": self.quit_app.emit,
        }

        self.hotkey_actions.clear()

        for action, signal_func in shortcuts.items():
            shortcut = self.config.get_shortcut(action)
            if shortcut:
                keys = self._parse_shortcut(shortcut)
                if keys:
                    self.hotkey_actions[frozenset(keys)] = signal_func

    def _normalize_key(self, key):
        """Normalize key to handle left/right modifiers.

        Args:
            key: Keyboard key

        Returns:
            Normalized key
        """
        # Map right modifiers to left for consistency
        if key == keyboard.Key.ctrl_r:
            return keyboard.Key.ctrl_l
        elif key == keyboard.Key.shift_r:
            return keyboard.Key.shift_l
        elif key == keyboard.Key.alt_r:
            return keyboard.Key.alt_l
        return key

    def _on_press(self, key):
        """Handle key press events.

        Args:
            key: Pressed key
        """
        try:
            key = self._normalize_key(key)
            self.current_keys.add(key)

            # Check if current combination matches any hotkey
            current_combo = frozenset(self.current_keys)
            if current_combo in self.hotkey_actions:
                self.hotkey_actions[current_combo]()
        except Exception as e:
            print(f"Error in key press handler: {e}")

    def _on_release(self, key):
        """Handle key release events.

        Args:
            key: Released key
        """
        try:
            key = self._normalize_key(key)
            self.current_keys.discard(key)
        except Exception as e:
            print(f"Error in key release handler: {e}")

    def start(self):
        """Start listening for global hotkeys."""
        if self.listener is None:
            self.listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release
            )
            self.listener.start()

    def stop(self):
        """Stop listening for global hotkeys."""
        if self.listener is not None:
            self.listener.stop()
            self.listener = None

    def reload_hotkeys(self):
        """Reload hotkeys from configuration."""
        self._setup_hotkeys()
