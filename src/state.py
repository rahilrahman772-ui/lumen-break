"""Tiny JSON-backed persistence for high score and settings."""
import json
import os
from . import constants as C

_DEFAULTS = {
    "high_score": 0,
    "volume": 0.7,
    "effects_intensity": 0.8,
    "fullscreen": False,
}


class Save:
    def __init__(self):
        appdata = os.environ.get("APPDATA")
        if appdata:
            save_dir = os.path.join(appdata, "LumenBreak")
            try:
                os.makedirs(save_dir, exist_ok=True)
            except OSError:
                save_dir = None

            if save_dir:
                self.path = os.path.join(save_dir, C.SAVE_FILE)
            else:
                self.path = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "..",
                    C.SAVE_FILE,
                )
        else:
            self.path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "..",
                C.SAVE_FILE,
            )

        self.data = dict(_DEFAULTS)
        self.load()

    def load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r") as f:
                    loaded = json.load(f)
                self.data.update({k: loaded.get(k, v) for k, v in _DEFAULTS.items()})
            except (json.JSONDecodeError, OSError):
                pass

    def save(self):
        try:
            with open(self.path, "w") as f:
                json.dump(self.data, f, indent=2)
        except OSError:
            pass

    def get(self, key):
        return self.data.get(key, _DEFAULTS.get(key))

    def set(self, key, value):
        self.data[key] = value
        self.save()
