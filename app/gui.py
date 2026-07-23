import sys, os
import tkinter as tk
from tkinter import ttk, messagebox
from typing import List

from .file_manager import list_macros, save_macro, load_macro, delete_macro
from .macro_engine import MacroEngine
from .models import MacroEvent
from .hotkeys import HotkeyManager
from .utils import is_valid_macro_name

def resource_path(relative_path):
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

class MacroApp(tk.Tk):
    STATE_IDLE = "idle"
    STATE_RECORDING = "recording"
    STATE_PLAYING = "playing"

    def __init__(self):
        super().__init__()
        self.title("Macro Recorder")

        # icon
        try:
            self.iconbitmap(resource_path("assets/record.ico"))
        except tk.TclError:
            pass

        # window size
        try:
            dpi = self.winfo_fpixels('1i')
            scaling = dpi / 72.0
        except tk.TclError:
            scaling = 1.0
        self.tk.call('tk', 'scaling', scaling)
        self.geometry("500x520")
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

        self.create_menu()
        self.create_widgets()

        # In‑window hotkeys
        self.bind('<F8>', self.record_callback)
        self.bind('<F9>', self.stop_callback)
        self.bind('<F10>', self.play_callback)

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.refresh_macro_list()
        self.update_ui_state()
        self.status_label.config(text="Ready")
        self.playing_label.config(text="")  # clear playing indicator
        self.recording_label.config(text="")  # clear recording indicator

    def create_menu(self):
        menubar = tk.Menu(self)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Save Macro", command=self.save_callback)
        file_menu.add_command(label="Load Macro", command=self.load_callback)
        file_menu.add_command(label="Delete Macro", command=self.delete_callback)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_close)
        menubar.add_cascade(label="File", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="Shortcuts", command=self.show_shortcuts)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.config(menu=menubar)

    def show_shortcuts(self):
        messagebox.showinfo(
            "Keyboard Shortcuts",
            "F8  —  Record\nF9  —  Stop\nF10 —  Play\n\n"
            "These hotkeys work globally, even when the window isn't focused."
        )

    def create_widgets(self):
        # ---------- Top Frame: File name + Save/Load/Delete ---------- #
        top_frame = ttk.Frame(self, padding=(10, 10, 10, 6))
        top_frame.pack(fill='x')

        ttk.Label(top_frame, text="Macro Name:").pack(side='left', padx=(0, 5))

        self.filename_entry = ttk.Entry(top_frame, textvariable=self.filename_var, width=16)
        self.filename_entry.pack(side='left', padx=5)

        self.save_btn = ttk.Button(top_frame, text="Save", width=7, command=self.save_callback)
        self.save_btn.pack(side='left', padx=3)

        self.load_btn = ttk.Button(top_frame, text="Load", width=7, command=self.load_callback)
        self.load_btn.pack(side='left', padx=3)

        self.delete_btn = ttk.Button(top_frame, text="Delete", width=7, command=self.delete_callback)
        self.delete_btn.pack(side='left', padx=3)

        ttk.Separator(self, orient='horizontal').pack(fill='x', padx=10)

        # ---------- Middle Frame: List of saved macros ---------- #
        middle_frame = ttk.Frame(self, padding=(10, 8, 10, 8))
        middle_frame.pack(fill='both', expand=True)

        ttk.Label(middle_frame, text="Saved Macros:").pack(anchor='w', pady=(0, 5))

        list_frame = ttk.Frame(middle_frame)
        list_frame.pack(fill='both', expand=True)

        self.macro_listbox = tk.Listbox(list_frame, height=8, selectmode=tk.SINGLE)
        self.macro_listbox.pack(side='left', fill='both', expand=True)
        self.macro_listbox.bind('<Double-Button-1>', self.load_callback)

        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.macro_listbox.yview)
        scrollbar.pack(side='right', fill='y')
        self.macro_listbox.config(yscrollcommand=scrollbar.set)

        ttk.Separator(self, orient='horizontal').pack(fill='x', padx=10)

        # ---------- Bottom Frame: Record/Stop/Play + Loop ---------- #
        bottom_frame = ttk.Frame(self, padding=(10, 8, 10, 4))
        bottom_frame.pack(fill='x')

        self.record_btn = ttk.Button(bottom_frame, text="⏺ Record", command=self.record_callback)
        self.record_btn.pack(side='left', padx=3)

        self.stop_btn = ttk.Button(bottom_frame, text="⏹ Stop", command=self.stop_callback)
        self.stop_btn.pack(side='left', padx=3)

        self.play_btn = ttk.Button(bottom_frame, text="▶ Play", command=self.play_callback)
        self.play_btn.pack(side='left', padx=3)

        self.loop_check = ttk.Checkbutton(bottom_frame, text="Loop playback", variable=self.loop_var)
        self.loop_check.pack(side='left', padx=(15, 0))

        hint_frame = ttk.Frame(self, padding=(10, 0, 10, 4))
        hint_frame.pack(fill='x')
        ttk.Label(
            hint_frame, text="F8 Record   ·   F9 Stop   ·   F10 Play",
            font=('TkDefaultFont', 8), foreground='gray40'
        ).pack(anchor='w')

        # ---------- "Now Recording" / "Now Playing" indicators ---------- #
        self.recording_label = ttk.Label(self, text="", font=('TkDefaultFont', 9, 'bold'), foreground='red')
        self.recording_label.pack(side='bottom', anchor='w', padx=10, pady=(0, 2))

        self.playing_label = ttk.Label(self, text="", font=('TkDefaultFont', 9, 'bold'), foreground='blue')
        self.playing_label.pack(side='bottom', anchor='w', padx=10, pady=(0, 2))

        # ---------- Status Bar ---------- #
        self.status_label = ttk.Label(self, text="", relief='sunken', anchor='w')
        self.status_label.pack(side='bottom', fill='x', padx=10, pady=(4, 10))

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
        self.after(0, lambda: self.recording_label.config(text=""))
        if events:
            self.after(0, self._set_state_idle)
        else:
            self.after(0, self._set_state_idle)

    def _on_playback_finished(self):
        self.after(0, self._set_state_idle)
        self.after(0, lambda: self.playing_label.config(text=""))  # clear playing indicator

    def _set_state_idle(self):
        self.state = self.STATE_IDLE
        self.update_ui_state()
        self.status_label.config(text="Ready")
        # Clear the recording/playing indicators if still showing
        self.recording_label.config(text="")
        self.playing_label.config(text="")

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

        # ----- require a filename before recording ----- #
        name = self.filename_var.get().strip()
        if not is_valid_macro_name(name):
            messagebox.showwarning(
                "Name Required",
                "Please enter a valid macro name before recording."
            )
            self.filename_entry.focus_set()
            return

        self.state = self.STATE_RECORDING
        self.update_ui_state()
        self.recording_label.config(text=f"● Recording: {name}")
        self.engine.start_recording()

    def stop_callback(self, event=None):
        if self.state == self.STATE_IDLE:
            return
        if self.engine.is_recording():
            self.engine.stop_recording()
            self.recording_label.config(text="")  # clear recording indicator
        elif self.engine.is_playing():
            self.engine.stop_playback()
            self.playing_label.config(text="")  # clear playing indicator

    def play_callback(self, event=None):
        if self.state != self.STATE_IDLE:
            return
        if not self.engine.playback_events:
            messagebox.showinfo("No Macro Loaded", "Please load a macro or record one first.")
            return

        # Show which macro is playing
        name = self.filename_var.get().strip()
        if name:
            self.playing_label.config(text=f"▶ Playing: {name}")
            try:
                idx = self.macro_listbox.get(0, tk.END).index(name)
                self.macro_listbox.selection_clear(0, tk.END)
                self.macro_listbox.selection_set(idx)
                self.macro_listbox.see(idx)
            except ValueError:
                pass
        else:
            self.playing_label.config(text="▶ Playing (unsaved)")

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
            self.after(200, self._really_close)
        else:
            self._really_close()

    def _really_close(self):
        self.hotkey_manager.stop()
        self.destroy()