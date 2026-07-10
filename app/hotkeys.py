# hotkeys.py
import threading
import time
from typing import Callable, Optional

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    print("Warning: 'keyboard' library not installed. Global hotkeys will not work.")


class HotkeyManager:
    """
    Registers global hotkeys for F8 (record), F9 (stop), F10 (play).
    All callbacks are invoked from a background thread – the caller must
    use thread-safe mechanisms (e.g., Tk's `after`) to update GUI widgets.
    """

    def __init__(self,
                 on_record: Optional[Callable] = None,
                 on_stop: Optional[Callable] = None,
                 on_play: Optional[Callable] = None):
        self.on_record = on_record
        self.on_stop = on_stop
        self.on_play = on_play
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """Start the hotkey listener in a background thread."""
        if not KEYBOARD_AVAILABLE:
            return
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._listener_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the hotkey listener."""
        self._running = False
        # The keyboard library's listener can be stopped by calling keyboard.unhook_all()
        # but we want to keep the listener running until we explicitly stop.
        # We'll rely on the thread exiting when _running becomes False.
        # However, keyboard.read_key() blocks. We'll use a different approach:
        # We'll register hotkeys with keyboard.add_hotkey and keep them active.
        # That way we don't need a blocking loop; we just add and later remove.
        # This is cleaner.
        # So we'll change the implementation to use add_hotkey / remove_hotkey.
        # Let's rewrite:
    
    # Better implementation using keyboard.add_hotkey and keyboard.remove_hotkey
    def start(self):
        if not KEYBOARD_AVAILABLE:
            return
        if self._running:
            return
        self._running = True
        # Register hotkeys
        self._hotkey_ids = []
        if self.on_record:
            self._hotkey_ids.append(keyboard.add_hotkey('f8', self._wrap_callback(self.on_record)))
        if self.on_stop:
            self._hotkey_ids.append(keyboard.add_hotkey('f9', self._wrap_callback(self.on_stop)))
        if self.on_play:
            self._hotkey_ids.append(keyboard.add_hotkey('f10', self._wrap_callback(self.on_play)))

    def stop(self):
        if not KEYBOARD_AVAILABLE:
            return
        if not self._running:
            return
        self._running = False
        # Remove all registered hotkeys
        for id in getattr(self, '_hotkey_ids', []):
            keyboard.remove_hotkey(id)
        self._hotkey_ids = []

    def _wrap_callback(self, callback):
        """Wrap a callback so that it doesn't crash and we can log if needed."""
        def wrapper():
            try:
                callback()
            except Exception as e:
                print(f"Hotkey callback error: {e}")
        return wrapper