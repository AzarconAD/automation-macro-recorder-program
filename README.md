# Macro Recorder
Made by: Adam Daniel P. Azarcon

A simple desktop macro recorder built with Python and Tkinter.  
Record keyboard and mouse actions, play them back with optional looping, and manage saved macros with a clean GUI.

---

## Features

- **Record** mouse clicks, keyboard presses, and mouse movements.
- **Play** recorded macros with adjustable timing.
- **Loop** playback infinitely until stopped.
- **Global hotkeys** – F8 to record, F9 to stop, F10 to play (work even when window is not focused).
- **Save, Load, Delete** macros – stored as JSON files.
- **Visual indicators** for recording/playing status.
- **Keyboard shortcuts menu** accessible via the Help menu.

---

## Installation

### 1. Clone or download the project

```bash
git clone <repository-url>
cd macro-recorder
```

### 2. Create a virtual environment (optional but recommended)

```bash
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
python main.py
```

---

## Usage

1. **Enter a macro name** – required before recording.  
2. **Press F8** (or click **Record**) to start capturing input.  
3. **Perform your actions** – keyboard, mouse clicks, scrolls, and movements.  
4. **Press F9** (or click **Stop**) to finish recording.  
5. **Press F10** (or click **Play**) to replay the recorded macro.  
6. **Check "Loop"** if you want the macro to repeat until stopped.  
7. **Save** the macro to disk for later use (JSON format).  
8. **Load** a saved macro from the list or double‑click its name.  
9. **Delete** unwanted macros.

All buttons are disabled during recording/playback to prevent conflicts.

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| F8  | Start recording |
| F9  | Stop recording / playback |
| F10 | Play the loaded macro |

Hotkeys work globally – you can use them while any other application is active.

---

## File Structure

```
macro-recorder/
├── app/
│   ├── __init__.py
│   ├── config.py           # Constants (paths, hotkey names)
│   ├── file_manager.py     # Save/Load/Delete/List macros (JSON)
│   ├── gui.py              # Tkinter GUI with all controls
│   ├── hotkeys.py          # Global hotkey registration
│   ├── macro_engine.py     # Core recording/playback logic
│   ├── models.py           # MacroEvent data class + JSON helpers
│   └── utils.py            # Validation helpers (filename check)
├── data/                   # Folder where macros are stored (created automatically)
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
└── README.md               # This file
```

---

## Dependencies

See [`requirements.txt`](requirements.txt) for a full list.

- `pynput` – for low‑level keyboard/mouse capture and simulation.
- `keyboard` – for global hotkey support (F8, F9, F10).

---

## Troubleshooting

- **Global hotkeys not working?**  
  On Linux, you may need to run with `sudo` (e.g., `sudo python main.py`) because the `keyboard` library requires root privileges for global hooks. On Windows, it usually works without elevation.

- **Mouse movements not recorded?**  
  By default, the app records mouse movement events. If you see performance issues, you can disable that in `macro_engine.py` by commenting out the `on_move` listener.

- **Macro playback timing off?**  
  The replay timing is based on the timestamp of each event relative to the start of recording. If your system is busy, playback may be slightly delayed; but it should match the original timing closely.

---

## License

This project is open source and available under the MIT License.

---

## Contributing

Feel free to open issues or submit pull requests with improvements.  
Suggestions for additional features are welcome!