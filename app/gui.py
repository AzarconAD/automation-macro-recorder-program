import tkinter as tk
from tkinter import ttk, messagebox


class MacroApp(tk.Tk):
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

        self.create_widgets()

        # hotkeys
        self.bind('<F8>', self.record_callback)
        self.bind('<F9>', self.stop_callback)
        self.bind('<F10>', self.play_callback)


        self.refresh_macro_list()

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

    # -------------------- Callbacks (placeholders) --------------------
    def save_callback(self):
        """Save the currently recorded macro."""
        name = self.filename_var.get().strip()
        if not name:
            messagebox.showwarning("Missing Name", "Please enter a macro name.")
            return
        self.status_label.config(text=f"Saving macro '{name}'...")
        # TODO: connect to file_manager.save_macro()

    def load_callback(self):
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
            self.refresh_macro_list()

    def record_callback(self, event=None):
        """Start recording (bound to F8 and Record button)."""
        self.status_label.config(text="Recording... (press F9 to stop)")
        # TODO: start macro_engine.record()

    def stop_callback(self, event=None):
        """Stop recording or playback (bound to F9 and Stop button)."""
        self.status_label.config(text="Stopped.")
        # TODO: stop macro_engine (recording or playback)

    def play_callback(self, event=None):
        """Play the loaded macro (bound to F10 and Play button)."""
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