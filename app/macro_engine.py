import time
import threading
from typing import List, Optional, Callable

from pynput import mouse, keyboard
from pynput.mouse import Button as MouseButton
from pynput.keyboard import Key as KeyboardKey, KeyCode

from .models import MacroEvent
from .config import HOTKEY_RECORD, HOTKEY_STOP, HOTKEY_PLAY


class MacroEngine:
    """
    Handles recording and playback. All callbacks are invoked from the engine's
    background threads; the GUI should use `after()` to update widgets safely.
    """

    def __init__(self,
                 status_callback: Optional[Callable[[str], None]] = None,
                 on_recording_stopped: Optional[Callable[[List[MacroEvent]], None]] = None,
                 on_playback_finished: Optional[Callable[[], None]] = None):
        self.status_callback = status_callback or (lambda msg: print(msg))
        self.on_recording_stopped = on_recording_stopped or (lambda events: None)
        self.on_playback_finished = on_playback_finished or (lambda: None)

        # Recording state
        self.recording = False
        self.recorded_events: List[MacroEvent] = []
        self.record_start_time = 0.0
        self.keyboard_listener = None
        self.mouse_listener = None

        # Playback state
        self.playing = False
        self.loop = False
        self.playback_events: List[MacroEvent] = []
        self.playback_thread: Optional[threading.Thread] = None
        self._stop_playback_requested = False

        # Hotkey keys (to filter out of recording)
        self._hotkey_keys = {HOTKEY_RECORD, HOTKEY_STOP, HOTKEY_PLAY}

    # -------------------- Recording -------------------- #
    def start_recording(self):
        if self.recording:
            return
        self.recording = True
        self.recorded_events = []
        self.record_start_time = time.time()
        self.status_callback("Recording started...")

        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.mouse_listener = mouse.Listener(
            on_click=self._on_mouse_click,
            on_move=self._on_mouse_move,
            on_scroll=self._on_mouse_scroll
        )
        self.keyboard_listener.start()
        self.mouse_listener.start()

    def stop_recording(self):
        if not self.recording:
            return
        self.recording = False
        if self.keyboard_listener and self.keyboard_listener.running:
            self.keyboard_listener.stop()
        if self.mouse_listener and self.mouse_listener.running:
            self.mouse_listener.stop()
        self.keyboard_listener = None
        self.mouse_listener = None

        count = len(self.recorded_events)
        self.status_callback(f"Recording stopped. {count} events captured.")
        if self.recorded_events:
            self.playback_events = self.recorded_events.copy()

        self.on_recording_stopped(self.recorded_events)

    # ---------- Recording callbacks ---------- #
    def _record_event(self, event_type, action, key=None, button=None, x=None, y=None):
        if not self.recording:
            return

        # Filter out hotkey events (F8, F9, F10) so they don't get saved
        if event_type == 'keyboard' and key in self._hotkey_keys:
            return

        timestamp = time.time() - self.record_start_time
        ev = MacroEvent(
            event_type=event_type,
            action=action,
            key=key,
            button=button,
            x=x,
            y=y,
            timestamp=timestamp
        )
        self.recorded_events.append(ev)

    def _on_key_press(self, key):
        try:
            key_str = key.char if isinstance(key, KeyCode) else key.name
        except AttributeError:
            key_str = str(key)
        self._record_event('keyboard', 'press', key=key_str)

    def _on_key_release(self, key):
        try:
            key_str = key.char if isinstance(key, KeyCode) else key.name
        except AttributeError:
            key_str = str(key)
        self._record_event('keyboard', 'release', key=key_str)

    def _on_mouse_click(self, x, y, button, pressed):
        action = 'press' if pressed else 'release'
        self._record_event('mouse', action, button=button.name, x=x, y=y)

    def _on_mouse_move(self, x, y):
        self._record_event('mouse', 'move', x=x, y=y)

    def _on_mouse_scroll(self, x, y, dx, dy):
        self._record_event('mouse', 'scroll', button='scroll', x=dx, y=dy)

    # -------------------- Playback -------------------- #
    def play_macro(self, events: List[MacroEvent], loop: bool = False):
        if self.playing:
            self.stop_playback()
        if not events:
            self.status_callback("No events to play.")
            return

        self.playback_events = events
        self.loop = loop
        self.playing = True
        self._stop_playback_requested = False
        self.status_callback("Playback started.")

        self.playback_thread = threading.Thread(target=self._playback_worker, daemon=True)
        self.playback_thread.start()

    def stop_playback(self):
        if self.playing:
            self._stop_playback_requested = True
            self.status_callback("Stopping playback...")

    def _playback_worker(self):
        controller = keyboard.Controller()
        mouse_controller = mouse.Controller()

        while self.playing and not self._stop_playback_requested:
            start_time = time.time()
            # Play all events once
            for ev in self.playback_events:
                if self._stop_playback_requested or not self.playing:
                    break
                now = time.time() - start_time
                sleep_time = ev.timestamp - now
                if sleep_time > 0:
                    time.sleep(sleep_time)
                self._replay_event(ev, controller, mouse_controller)

            # If loop is disabled or we were stopped, exit the outer loop
            if not self.loop or self._stop_playback_requested:
                break

        self.playing = False
        self._stop_playback_requested = False
        self.status_callback("Playback finished.")
        self.on_playback_finished()

    def _replay_event(self, ev: MacroEvent, kb_controller, mouse_controller):
        try:
            if ev.event_type == 'keyboard':
                key = self._str_to_key(ev.key)
                if key is None:
                    return
                if ev.action == 'press':
                    kb_controller.press(key)
                else:
                    kb_controller.release(key)

            elif ev.event_type == 'mouse':
                if ev.button == 'scroll':
                    mouse_controller.scroll(ev.x, ev.y)
                elif ev.action == 'move':
                    mouse_controller.position = (ev.x, ev.y)
                else:  # click press/release
                    button = self._str_to_mouse_button(ev.button)
                    if button is None:
                        return
                    if ev.action == 'press':
                        mouse_controller.press(button)
                    else:
                        mouse_controller.release(button)
        except Exception as e:
            print(f"Replay error: {e}")

    @staticmethod
    def _str_to_key(key_str: str):
        if key_str is None:
            return None
        try:
            return getattr(KeyboardKey, key_str)
        except AttributeError:
            pass
        try:
            return KeyCode.from_char(key_str)
        except:
            return None

    @staticmethod
    def _str_to_mouse_button(button_str: str):
        if button_str is None:
            return None
        try:
            return getattr(MouseButton, button_str)
        except AttributeError:
            return None

    # -------------------- Utility -------------------- #
    def is_recording(self) -> bool:
        return self.recording

    def is_playing(self) -> bool:
        return self.playing

    def get_recorded_events(self) -> List[MacroEvent]:
        return self.recorded_events