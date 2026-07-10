import tkinter as tk
from tkinter import ttk, messagebox
from typing import List

from .file_manager import list_macros, save_macro, load_macro, delete_macro
from .macro_engine import MacroEngine
from .models import MacroEvent
from .hotkeys import HotkeyManager
from .utils import is_valid_macro_name

class MacroApp(tk.Tk):

    # Simple state machine so buttons can't fire out-of-order actions
    # (e.g. clicking Play while a recording is in progress).
    STATE_IDLE = "idle"
    STATE_RECORDING = "recording"
    STATE_PLAYING = "playing"

    def __init__(self):
        super().__init__()
        self.title("Macro Programmer")
        self.geometry("600x500")
        self.resizable(False, False)

        style = ttk.Style()
        try:
            style.theme_use('clam')
        except tk.TclError:
            pass

        # variables
        self.loop_var = tk.BooleanVar(value=False)
        self.filename_var = tk.StringVar()
        self.state = self.STATE_IDLE

        self.engine = MacroEngine(
            status_callback=self._safe_status_update,
            on_recording_stopped=self._on_recording_stopped,
            on_playback_finished=self._on_playback_finished
        )

        # Global hotkey manager
        self.hotkey_manager = HotkeyManager(
            on_record=self._safe_record,
            on_stop=self._safe_stop,
            on_play=self._safe_play
        )
        self.hotkey_manager.start()

        self.create_widgets()

        # In‑window hotkeys
        self.bind('<F8>', self.record_callback)
        self.bind('<F9>', self.stop_callback)
        self.bind('<F10>', self.play_callback)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.refresh_macro_list()
        self.update_ui_state()
        self.status_label.config(text="Ready")

    def create_widgets(self):
        top_frame = ttk.Frame(self, padding="10")
        top_frame.pack(fill='x')

        ttk.Label(top_frame, text="Macro Name:").pack(side='left', padx=(0, 5))

        self.filename_entry = ttk.Entry(top_frame, textvariable=self.filename_var, width=25)
        self.filename_entry.pack(side='left', padx=5)

        self.save_btn = ttk.Button(top_frame, text="Save", command=self.save_callback)
        self.save_btn.pack(side='left', padx=5)

        self.load_btn = ttk.Button(top_frame, text="Load", command=self.load_callback)
        self.load_btn.pack(side='left', padx=5)

        self.delete_btn = ttk.Button(top_frame, text="Delete", command=self.delete_callback)
        self.delete_btn.pack(side='left', padx=5)

        middle_frame = ttk.Frame(self, padding="10")
        middle_frame.pack(fill='both', expand=True)

        ttk.Label(middle_frame, text="Saved Macros:").pack(anchor='w', pady=(0, 5))

        list_frame = ttk.Frame(middle_frame)
        list_frame.pack(fill='both', expand=True)

        self.macro_listbox = tk.Listbox(list_frame, height=12, selectmode=tk.SINGLE)
        self.macro_listbox.pack(side='left', fill='both', expand=True)
        self.macro_listbox.bind('<Double-Button-1>', self.load_callback)

        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.macro_listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.macro_listbox.config(yscrollcommand=scrollbar.set)

        bottom_frame = ttk.Frame(self, padding="10")
        bottom_frame.pack(fill='x')

        self.record_btn = ttk.Button(bottom_frame, text="Record (F8)", command=self.record_callback)
        self.record_btn.pack(side='left', padx=5)

        self.stop_btn = ttk.Button(bottom_frame, text="Stop (F9)", command=self.stop_callback)
        self.stop_btn.pack(side='left', padx=5)

        self.play_btn = ttk.Button(bottom_frame, text="Play (F10)", command=self.play_callback)
        self.play_btn.pack(side='left', padx=5)

        self.loop_check = ttk.Checkbutton(bottom_frame, text="Loop", variable=self.loop_var)
        self.loop_check.pack(side='left', padx=20)

        self.status_label = ttk.Label(self, text="", relief='sunken', anchor='w')
        self.status_label.pack(side='bottom', fill='x', padx=10, pady=(0, 10))

    # -------------------- UI state helpers -------------------- #
    def update_ui_state(self):
        busy = self.state in (self.STATE_RECORDING, self.STATE_PLAYING)
        self.record_btn.config(state='disabled' if busy else 'normal')
        self.play_btn.config(state='disabled' if busy else 'normal')
        self.stop_btn.config(state='normal' if busy else 'disabled')
        for widget in (self.save_btn, self.load_btn, self.delete_btn, self.filename_entry):
            widget.config(state='disabled' if busy else 'normal')

    # -------------------- Thread‑safe wrappers for hotkeys -------------------- #
    def _safe_record(self):
        self.after(0, self.record_callback)

    def _safe_stop(self):
        self.after(0, self.stop_callback)

    def _safe_play(self):
        self.after(0, self.play_callback)

    def _safe_status_update(self, msg: str):
        self.after(0, lambda: self.status_label.config(text=msg))

    def _on_recording_stopped(self, events: List[MacroEvent]):
        if events:
            self.filename_var.set("")  # clear the name, since this is unsaved
            self.status_label.config(text=f"Recorded {len(events)} events – ready to play.")
        self.after(0, self._set_state_idle)

    def _on_playback_finished(self):
        self.after(0, self._set_state_idle)

    def _set_state_idle(self):
        self.state = self.STATE_IDLE
        self.update_ui_state()
        self.status_label.config(text="Ready")

    # -------------------- Core actions -------------------- #
    def save_callback(self):
        name = self.filename_var.get().strip()
        if not is_valid_macro_name(name):
            messagebox.showwarning(
                "Invalid Name",
                "Please enter a valid macro name (letters, numbers, spaces, '-' and '_' only; no slashes)."
            )
            return

        events = self.engine.get_recorded_events()
        if not events:
            messagebox.showinfo("No Events", "No recorded events to save. Record something first.")
            return

        existing = list_macros()
        if name in existing:
            if not messagebox.askyesno("Overwrite Macro", f"A macro named '{name}' already exists. Overwrite?"):
                return

        try:
            save_macro(name, events)
            self.status_label.config(text=f"Macro '{name}' saved.")
            self.refresh_macro_list()
        except Exception as e:
            messagebox.showerror("Save Error", f"Could not save macro: {e}")

    def load_callback(self, event=None):
        selection = self.macro_listbox.curselection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a macro from the list.")
            return
        name = self.macro_listbox.get(selection[0])
        try:
            events = load_macro(name)
            self.engine.playback_events = events
            self.filename_var.set(name)
            self.status_label.config(text=f"Loaded macro '{name}' ({len(events)} events).")
        except Exception as e:
            messagebox.showerror("Load Error", f"Could not load macro: {e}")

    def delete_callback(self):
        selection = self.macro_listbox.curselection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a macro to delete.")
            return
        name = self.macro_listbox.get(selection[0])
        if messagebox.askyesno("Confirm Delete", f"Delete macro '{name}'?"):
            try:
                delete_macro(name)
                self.status_label.config(text=f"Deleted macro '{name}'.")
                if self.filename_var.get().strip() == name:
                    self.filename_var.set("")
                self.refresh_macro_list()
            except Exception as e:
                messagebox.showerror("Delete Error", f"Could not delete macro: {e}")

    def record_callback(self, event=None):
        if self.state != self.STATE_IDLE:
            return
        self.state = self.STATE_RECORDING
        self.update_ui_state()
        self.engine.start_recording()

    def stop_callback(self, event=None):
        if self.state == self.STATE_IDLE:
            return
        if self.engine.is_recording():
            self.engine.stop_recording()
        elif self.engine.is_playing():
            self.engine.stop_playback()
        # The engine's callbacks will reset the state to idle

    def play_callback(self, event=None):
        if self.state != self.STATE_IDLE:
            return
        if not self.engine.playback_events:
            messagebox.showinfo("No Macro Loaded", "Please load a macro before playing.")
            return
        self.state = self.STATE_PLAYING
        self.update_ui_state()
        loop = self.loop_var.get()
        self.engine.play_macro(self.engine.playback_events, loop=loop)

    def refresh_macro_list(self):
        self.macro_listbox.delete(0, tk.END)
        for name in list_macros():
            self.macro_listbox.insert(tk.END, name)

    def on_close(self):
        if self.state != self.STATE_IDLE:
            if not messagebox.askyesno("Quit", "A macro is still recording/playing. Stop and quit?"):
                return
            self.stop_callback()
            # Give time for threads to finish before destroying
            self.after(200, self._really_close)
        else:
            self._really_close()

    def _really_close(self):
        self.hotkey_manager.stop()
        self.destroy()