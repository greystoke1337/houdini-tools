# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Houdini HOTAS Control — a Python package that lets a HOTAS (joystick + throttle) drive the Houdini network editor. The joystick moves the cursor and shoots nodes; the throttle scrolls/zooms; a physics sim blasts existing nodes away on each shot.

**Hardware targeted:**
- VKB Gladiator EVO R (joystick) — VID `0x231D` / PID `0x0200`
- Thrustmaster Warthog Throttle — VID `0x044F` / PID `0x0404`

## Setup

```bash
pip install hid          # hidapi Python binding
pip install PySide6      # or PySide2 — already bundled in Houdini
```

The package is not installed; add `C:\Users\maxim\houdini-tools` to `sys.path` inside Houdini.

## Running

**Inside Houdini** — run `shelf_tool.py` once in the Python shell to create shelf buttons, then use the shelf. Or paste the `*_code` strings from `shelf_tool.py` directly into shelf buttons.

**Outside Houdini (HID diagnostics):**
```bash
# List all HID devices + watch report bytes
python -m houdini_hotas_control.hid_scan

# Scan Warthog throttle axis range (run while sweeping throttle)
python throttle_scan.py
```

**Hot-reload during development** — use the "JOY Reload" shelf button; it stops both listeners, purges all `houdini_hotas_control.*` modules from `sys.modules`, then prints instructions to restart.

## Architecture

All live state is in module-level globals. No classes own the run loop.

| Module | Role |
|--------|------|
| `joystick.py` | `VKBJoystick` — opens HID, normalizes axes (12-bit, deadzone, EMA smoothing), reads trigger |
| `throttle.py` | `WarthogThrottle` — opens HID, normalizes throttle axis (14-bit, 0–1) |
| `throw.py` | Event loop callback: polls joystick → moves OS cursor via `mouse_event`, fires `_shoot()` on trigger, calls `physics.tick()` each frame |
| `node_sizer.py` | Event loop callback: polls throttle → converts position delta to `MOUSEEVENTF_WHEEL` scroll |
| `physics.py` | Per-node velocity sim in network space. `explode()` adds impulse; `tick()` integrates + damps; keyed by `node.path()` |
| `config.py` | Loads/saves `config.json`; applies values to module-level attrs on `throw`, `physics`, `node_sizer` by name |
| `gui.py` | PySide6/2 floating panel; sliders map directly to module-level attrs and call `config.save()` on every change |
| `hid_scan.py` | Dev tool — enumerate HID devices, watch raw report bytes to find axis byte offsets |

**Event loop integration:** `throw.start()` / `node_sizer.start()` both call `hou.ui.addEventLoopCallback()`. Houdini fires these ~60×/s. `stop()` calls `hou.ui.removeEventLoopCallback()`.

**Config flow:** `config.load()` reads `config.json` and `setattr`s values onto module globals by matching key names. `config.save()` does the reverse. The GUI triggers save on every slider move.

**Physics node tracking:** `_velocities` dict maps `node.path()` → `[vx, vy]`. Nodes that are deleted or renamed mid-sim are silently dropped in `tick()`.

## Key constants to know

Defined as module-level vars (overwritten by `config.load()`):

| Constant | Module | Default |
|----------|--------|---------|
| `SENSITIVITY` | `throw` | 20.0 |
| `RPM` | `throw` | 300.0 |
| `INVERT_Y` | `throw` | True |
| `EXPLOSION_FORCE` | `physics` | 10.0 |
| `EXPLOSION_RADIUS` | `physics` | 6.0 |
| `DAMPING` | `physics` | 0.88 |
| `SCROLL_SPEED` | `node_sizer` | 2400 |

## Adding a new HID device

1. Run `hid_scan.py` to find VID/PID and byte offsets.
2. Create a new class in a new file following `joystick.py` or `throttle.py` pattern.
3. Add VID/PID to `KNOWN` in `hid_scan.py`.
4. Wire a start/stop in `throw.py` or create a parallel module like `node_sizer.py`.
