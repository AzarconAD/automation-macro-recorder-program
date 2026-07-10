from typing import Callable, Optional

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    print("Warning: 'keyboard' library not installed. Global hotkeys will not work.")


class HotkeyManager:
    def __init__(self,
                 on_record: Optional[Callable] = None,
                 on_stop: Optional[Callable] = None,
                 on_play: Optional[Callable] = None):
        self.on_record = on_record
        self.on_stop = on_stop
        self.on_play = on_play
        self._running = False
        self._hotkey_ids = []

    def start(self):
        """Register global hotkeys using keyboard.add_hotkey."""
        if not KEYBOARD_AVAILABLE:
            return
        if self._running:
            return
        self._running = True
        self._hotkey_ids = []
        if self.on_record:
            self._hotkey_ids.append(
                keyboard.add_hotkey('f8', self._wrap_callback(self.on_record))
            )
        if self.on_stop:
            self._hotkey_ids.append(
                keyboard.add_hotkey('f9', self._wrap_callback(self.on_stop))
            )
        if self.on_play:
            self._hotkey_ids.append(
                keyboard.add_hotkey('f10', self._wrap_callback(self.on_play))
            )

    def stop(self):
        """Unregister all global hotkeys."""
        if not KEYBOARD_AVAILABLE:
            return
        if not self._running:
            return
        self._running = False
        for hotkey_id in self._hotkey_ids:
            keyboard.remove_hotkey(hotkey_id)
        self._hotkey_ids = []

    def _wrap_callback(self, callback):
        """Wrap a callback so that it doesn't crash and we can log if needed."""
        def wrapper():
            try:
                callback()
            except Exception as e:
                print(f"Hotkey callback error: {e}")
        return wrapper