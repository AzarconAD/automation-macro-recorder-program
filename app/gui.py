import re
import tkinter as tk
from tkinter import ttk, messagebox


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

        self.create_widgets()

        # hotkeys
        self.bind('<F8>', self.record_callback)
        self.bind('<F9>', self.stop_callback)
        self.bind('<F10>', self.play_callback)

        # Make sure a recording/playback in progress is stopped cleanly
        # if the user closes the window instead of pressing Stop.
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.refresh_macro_list()
        self.update_ui_state()

        self.status_label.config(text="Ready")

    def create_widgets(self):
        # ---------- Top Frame: File name + Save/Load/Delete ----------
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

        # ---------- Middle Frame: List of saved macros ----------
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

        # ---------- Bottom Frame: Record/Stop/Play + Loop ----------
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

        # ---------- Status Bar ----------
        self.status_label = ttk.Label(self, text="", relief='sunken', anchor='w')
        self.status_label.pack(side='bottom', fill='x', padx=10, pady=(0, 10))

    # -------------------- UI state helpers --------------------
    def update_ui_state(self):
        """Enable/disable controls based on current app state so the user
        can't trigger conflicting actions (e.g. Save while recording)."""
        busy = self.state in (self.STATE_RECORDING, self.STATE_PLAYING)

        self.record_btn.config(state='disabled' if busy else 'normal')
        self.play_btn.config(state='disabled' if busy else 'normal')
        self.stop_btn.config(state='normal' if busy else 'disabled')

        # Save/Load/Delete/rename shouldn't happen mid-recording or mid-playback
        for widget in (self.save_btn, self.load_btn, self.delete_btn, self.filename_entry):
            widget.config(state='disabled' if busy else 'normal')

    @staticmethod
    def is_valid_macro_name(name):
        """Reject names that would be unsafe/invalid as filenames
        (path separators, traversal sequences, empty/whitespace-only)."""
        if not name or not name.strip():
            return False
        if any(ch in name for ch in ('/', '\\', '..')):
            return False
        # Restrict to a conservative safe character set.
        return re.match(r'^[\w\-. ]+$', name) is not None

    # -------------------- Callbacks (placeholders) --------------------
    def save_callback(self):
        """Save the currently recorded macro."""
        name = self.filename_var.get().strip()

        if not self.is_valid_macro_name(name):
            messagebox.showwarning(
                "Invalid Name",
                "Please enter a valid macro name (letters, numbers, spaces, "
                "'-' and '_' only; no slashes)."
            )
            return

        existing = self.macro_listbox.get(0, tk.END)
        if name in existing:
            if not messagebox.askyesno(
                "Overwrite Macro", f"A macro named '{name}' already exists. Overwrite it?"
            ):
                return

        self.status_label.config(text=f"Saving macro '{name}'...")
        # TODO: connect to file_manager.save_macro()
        self.refresh_macro_list()

    def load_callback(self, event=None):
        """Load the selected macro from the list."""
        selection = self.macro_listbox.curselection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a macro from the list.")
            return
        name = self.macro_listbox.get(selection[0])
        self.filename_var.set(name)
        self.status_label.config(text=f"Loading macro '{name}'...")
        # TODO: connect to file_manager.load_macro()

    def delete_callback(self):
        """Delete the selected macro."""
        selection = self.macro_listbox.curselection()
        if not selection:
            messagebox.showinfo("No Selection", "Please select a macro to delete.")
            return
        name = self.macro_listbox.get(selection[0])
        if messagebox.askyesno("Confirm Delete", f"Delete macro '{name}'?"):
            self.status_label.config(text=f"Deleting macro '{name}'...")
            # TODO: connect to file_manager.delete_macro()

            # If the deleted macro was the one loaded in the name field,
            # clear it so Save/Play don't silently act on a stale name.
            if self.filename_var.get().strip() == name:
                self.filename_var.set("")

            self.refresh_macro_list()

    def record_callback(self, event=None):
        """Start recording (bound to F8 and Record button)."""
        if self.state != self.STATE_IDLE:
            return
        self.state = self.STATE_RECORDING
        self.update_ui_state()
        self.status_label.config(text="Recording... (press F9 to stop)")
        # TODO: start macro_engine.record()
        # NOTE: if macro_engine runs on a background thread, any status/UI
        # updates it triggers must go through self.after(...) rather than
        # touching widgets directly from that thread.

    def stop_callback(self, event=None):
        """Stop recording or playback (bound to F9 and Stop button)."""
        if self.state == self.STATE_IDLE:
            return
        self.state = self.STATE_IDLE
        self.update_ui_state()
        self.status_label.config(text="Stopped.")
        # TODO: stop macro_engine (recording or playback)

    def play_callback(self, event=None):
        """Play the loaded macro (bound to F10 and Play button)."""
        if self.state != self.STATE_IDLE:
            return
        if not self.filename_var.get().strip():
            messagebox.showinfo("No Macro Loaded", "Please load a macro before playing.")
            return

        self.state = self.STATE_PLAYING
        self.update_ui_state()
        loop = self.loop_var.get()
        self.status_label.config(text=f"Playing... (loop={loop})")
        # TODO: start macro_engine.play(loop=loop)

    def refresh_macro_list(self):
        """Update the listbox with names of saved macros."""
        self.macro_listbox.delete(0, tk.END)
        # TODO: replace with actual data from file_manager.list_macros()
        dummy_macros = ["macro1", "macro2", "example"]
        for name in dummy_macros:
            self.macro_listbox.insert(tk.END, name)

    def on_close(self):
        """Handle window close: make sure nothing is left running."""
        if self.state != self.STATE_IDLE:
            if not messagebox.askyesno(
                "Quit", "A macro is still recording/playing. Stop it and quit?"
            ):
                return
            self.stop_callback()
            # TODO: give macro_engine a moment to actually stop before destroy()
        self.destroy()