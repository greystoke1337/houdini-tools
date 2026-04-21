"""Persist tuning settings to disk as JSON."""

import json
import os

_PATH = os.path.join(os.path.dirname(__file__), "config.json")

_DEFAULTS = {
    "SENSITIVITY":      20.0,
    "RPM":             300.0,
    "INVERT_Y":         True,
    "EXPLOSION_FORCE":  10.0,
    "EXPLOSION_RADIUS":  6.0,
    "DAMPING":          0.88,
    "SCROLL_SPEED":     2400.0,
}


def load():
    """Apply saved settings to throw/physics modules. Safe to call before they're imported."""
    try:
        with open(_PATH) as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}

    from houdini_hotas_control import throw, physics, node_sizer
    for key, default in _DEFAULTS.items():
        value = data.get(key, default)
        for mod in (throw, physics, node_sizer):
            if hasattr(mod, key):
                setattr(mod, key, value)


def save():
    """Write current throw/physics settings to disk."""
    from houdini_hotas_control import throw, physics, node_sizer
    data = {}
    for key in _DEFAULTS:
        for mod in (throw, physics, node_sizer):
            if hasattr(mod, key):
                data[key] = getattr(mod, key)
                break
    with open(_PATH, "w") as f:
        json.dump(data, f, indent=2)
