# Houdini HOTAS Control

Drive the Houdini network editor with a HOTAS (joystick + throttle). Joystick moves the cursor and shoots nodes; throttle scrolls/zooms; a physics sim blasts existing nodes away on each shot.

**Targeted hardware:**
- VKB Gladiator EVO R (joystick) — VID `0x231D` / PID `0x0200`
- Thrustmaster Warthog Throttle — VID `0x044F` / PID `0x0404`

## Setup

```bash
pip install hid      # hidapi Python binding
pip install PySide6  # or PySide2 — already bundled in Houdini
```

Add `C:\path\to\houdini-tools` to `sys.path` inside Houdini (the package is not installed via pip).

## Running

**Inside Houdini** — run `shelf_tool.py` once in the Python shell to create shelf buttons, then use the shelf:

```python
import sys
sys.path.insert(0, r'C:\path\to\houdini-tools')
exec(open(r'C:\path\to\houdini-tools\houdini_hotas_control\shelf_tool.py').read())
```

Or paste the `*_code` strings from `shelf_tool.py` directly into shelf tool buttons.

**Outside Houdini (HID diagnostics):**

```bash
# List all HID devices and watch raw report bytes
python -m houdini_hotas_control.hid_scan

# Scan Warthog throttle axis range (run while sweeping the throttle)
python throttle_scan.py
```

**Hot-reload during development** — use the "JOY Reload" shelf button. It stops both listeners, purges all `houdini_hotas_control.*` modules from `sys.modules`, then prints instructions to restart.

## Controls

| Input | Action |
|-------|--------|
| Joystick X/Y | Move cursor |
| Trigger | Shoot a node at cursor position |
| Throttle axis | Scroll / zoom network view |

On each shot, nearby nodes are blasted outward with a physics impulse that damps over time.

## Tuning

Open the floating panel with `gui.show()` from a shelf button:

| Parameter | Default | Effect |
|-----------|---------|--------|
| Sensitivity | 20.0 | Cursor speed multiplier |
| RPM | 300.0 | Max fire rate |
| Explosion Force | 10.0 | Initial blast velocity |
| Explosion Radius | 6.0 | Blast radius in network units |
| Damping | 0.88 | Velocity decay per tick |
| Scroll Speed | 2400 | Throttle scroll multiplier |

Settings persist to `config.json` on every slider change.

## Architecture

All live state is in module-level globals. No classes own the run loop.

| Module | Role |
|--------|------|
| `joystick.py` | `VKBJoystick` — opens HID, normalizes axes (12-bit, deadzone, EMA smoothing), reads trigger |
| `throttle.py` | `WarthogThrottle` — opens HID, normalizes throttle axis (14-bit, 0-1) |
| `throw.py` | Event loop callback: polls joystick, moves OS cursor, fires `_shoot()` on trigger, calls `physics.tick()` |
| `node_sizer.py` | Event loop callback: polls throttle, sends `MOUSEEVENTF_WHEEL` scroll |
| `physics.py` | Per-node velocity sim in network space. `explode()` adds impulse; `tick()` integrates + damps |
| `config.py` | Loads/saves `config.json`; applies values to module-level attrs by name |
| `gui.py` | PySide6/2 floating panel; sliders map directly to module-level attrs |
| `hid_scan.py` | Dev tool — enumerate HID devices, watch raw bytes to find axis byte offsets |

`throw.start()` and `node_sizer.start()` register callbacks via `hou.ui.addEventLoopCallback()`. Houdini fires these ~60x/s.

## Adding a new HID device

1. Run `hid_scan.py` to find VID/PID and byte offsets.
2. Create a new class following the pattern in `joystick.py` or `throttle.py`.
3. Add VID/PID to `KNOWN` in `hid_scan.py`.
4. Wire start/stop in `throw.py` or create a parallel module like `node_sizer.py`.
