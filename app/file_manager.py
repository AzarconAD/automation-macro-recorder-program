import os
import json
from typing import List
from .models import MacroEvent, MacroEventEncoder, macro_event_decoder
from .config import DATA_DIR, FILE_EXT


def _get_filepath(name: str) -> str:
    safe_name = os.path.basename(name.strip())
    if not safe_name:
        raise ValueError("Invalid macro name")
    return os.path.join(DATA_DIR, f"{safe_name}{FILE_EXT}")

#--------file manager--------#
def list_macros() -> List[str]:
    if not os.path.exists(DATA_DIR):
        return []
    files = os.listdir(DATA_DIR)
    return sorted([f[:-len(FILE_EXT)] for f in files if f.endswith(FILE_EXT)])


def save_macro(name: str, events: List[MacroEvent]) -> None:
    filepath = _get_filepath(name)
    with open(filepath, 'w') as f:
        json.dump(events, f, cls=MacroEventEncoder, indent=2)


def load_macro(name: str) -> List[MacroEvent]:
    filepath = _get_filepath(name)
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Macro '{name}' not found.")
    with open(filepath, 'r') as f:
        return json.load(f, object_hook=macro_event_decoder)


def delete_macro(name: str) -> bool:
    filepath = _get_filepath(name)
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    return False