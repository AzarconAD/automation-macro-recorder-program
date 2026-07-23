import os
import sys

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATA_DIR = os.path.join(BASE_DIR, "data")
FILE_EXT = ".json"

HOTKEY_RECORD = "f8"
HOTKEY_STOP = "f9"
HOTKEY_PLAY = "f10"

os.makedirs(DATA_DIR, exist_ok=True)