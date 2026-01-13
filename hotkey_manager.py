"""Global hotkey manager using pynput."""
from pynput import keyboard
from typing import Callable, Dict
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QMetaObject, Qt, Q_ARG


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

    def _emit_signal_thread_safe(self, signal_name: str):
        """Emit a signal in a thread-safe way from pynput's background thread.

        Uses QMetaObject.invokeMethod with QueuedConnection to ensure the signal
        emission happens in the main Qt event loop thread.

        Args:
            signal_name: Name of the signal to emit
        """
        signal = getattr(self, signal_name, None)
        if signal:
            # Use invokeMethod to safely emit from background thread
            QMetaObject.invokeMethod(self, "_do_emit_" + signal_name, Qt.QueuedConnection)

    @pyqtSlot()
    def _do_emit_spotlight_toggle(self):
        """Thread-safe emit helper for spotlight_toggle signal."""
        print("Emitting spotlight_toggle signal (thread-safe)")
        self.spotlight_toggle.emit()

    @pyqtSlot()
    def _do_emit_draw_blue(self):
        """Thread-safe emit helper for draw_blue signal."""
        print("Emitting draw_blue signal (thread-safe)")
        self.draw_blue.emit()

    @pyqtSlot()
    def _do_emit_draw_red(self):
        """Thread-safe emit helper for draw_red signal."""
        print("Emitting draw_red signal (thread-safe)")
        self.draw_red.emit()

    @pyqtSlot()
    def _do_emit_draw_yellow(self):
        """Thread-safe emit helper for draw_yellow signal."""
        print("Emitting draw_yellow signal (thread-safe)")
        self.draw_yellow.emit()

    @pyqtSlot()
    def _do_emit_draw_green(self):
        """Thread-safe emit helper for draw_green signal."""
        print("Emitting draw_green signal (thread-safe)")
        self.draw_green.emit()

    @pyqtSlot()
    def _do_emit_clear_screen(self):
        """Thread-safe emit helper for clear_screen signal."""
        print("Emitting clear_screen signal (thread-safe)")
        self.clear_screen.emit()

    @pyqtSlot()
    def _do_emit_quit_app(self):
        """Thread-safe emit helper for quit_app signal."""
        print("Emitting quit_app signal (thread-safe)")
        self.quit_app.emit()

    def _setup_hotkeys(self):
        """Set up hotkey mappings from configuration."""
        # Build hotkey dictionary for GlobalHotKeys
        hotkeys = {}

        # Map action names to their corresponding emit method names
        signal_map = {
            "toggle_spotlight": "spotlight_toggle",
            "draw_blue": "draw_blue",
            "draw_red": "draw_red",
            "draw_yellow": "draw_yellow",
            "draw_green": "draw_green",
            "clear_screen": "clear_screen",
            "quit": "quit_app",
        }

        # Create wrapper functions to ensure proper thread-safe signal emission
        def make_callback(signal_name):
            """Create a callback that emits the signal thread-safely.

            Args:
                signal_name: Name of the signal to emit

            Returns:
                Callback function
            """
            def callback():
                print(f"Hotkey triggered for {signal_name}!")
                self._emit_signal_thread_safe(signal_name)
            return callback

        for action, signal_name in signal_map.items():
            shortcut = self.config.get_shortcut(action)
            if shortcut:
                hotkey_str = self._convert_shortcut(shortcut)
                hotkeys[hotkey_str] = make_callback(signal_name)
                print(f"Registered hotkey: {hotkey_str} for {action}")

        self.hotkeys = hotkeys
        print(f"Total hotkeys registered: {len(self.hotkeys)}")

    def start(self):
        """Start listening for global hotkeys."""
        if self.listener is None:
            try:
                self.listener = keyboard.GlobalHotKeys(self.hotkeys)
                # Set as daemon thread so it doesn't block application exit
                self.listener.daemon = True
                self.listener.start()
                print("Hotkey listener started successfully (daemon thread)")
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
