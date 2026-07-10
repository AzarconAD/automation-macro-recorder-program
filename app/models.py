import json
from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class MacroEvent:
    event_type: str          # 'keyboard' or 'mouse'
    action: str              # 'press', 'release', 'move', 'scroll'
    key: Optional[str] = None
    button: Optional[str] = None
    x: Optional[int] = None
    y: Optional[int] = None
    timestamp: float = 0.0

    def to_dict(self):
        return asdict(self)

    @classmethod
    def from_dict(cls, data):
        return cls(**data)


class MacroEventEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, MacroEvent):
            return obj.to_dict()
        return super().default(obj)


def macro_event_decoder(dct):
    if "event_type" in dct and "action" in dct:
        return MacroEvent.from_dict(dct)
    return dct