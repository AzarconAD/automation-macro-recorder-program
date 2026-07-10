# utils.py
import re

def is_valid_macro_name(name: str) -> bool:
    """
    Reject names that would be unsafe/invalid as filenames
    (path separators, traversal sequences, empty/whitespace-only).
    """
    if not name or not name.strip():
        return False
    if any(ch in name for ch in ('/', '\\', '..')):
        return False
    # Restrict to a conservative safe character set.
    return re.match(r'^[\w\-. ]+$', name) is not None