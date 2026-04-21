"""
Joystick-driven node shooter for Houdini.

Flow:
  1. start() registers _poll() with hou.ui.addEventLoopCallback()
  2. _poll() fires every Houdini UI tick (~60/s)
  3. Joystick X/Y moves the OS cursor via Win32 mouse_event
  4. Trigger rising edge -> create a node at the network editor cursor position
  5. stop() unregisters callback and closes HID device

Usage from Houdini shelf button:
  import sys
  sys.path.insert(0, r'C:\path\to\houdini-tools')
  from houdini_hotas_control import throw
  throw.start()          # default: shoots 'null' nodes
  # throw.start('geo')   # or any other node type
  # throw.stop()         # to stop
"""

import ctypes
import hou
from houdini_hotas_control.joystick import VKBJoystick
from houdini_hotas_control import physics

SENSITIVITY = 20.0
RPM = 300.0
INVERT_Y = True

_joystick: VKBJoystick | None = None
_node_type = "null"
_last_shot = 0.0


def _move_mouse(dx: float, dy: float) -> None:
    """Move cursor by (dx, dy) pixels relative to current position."""
    ctypes.windll.user32.mouse_event(
        0x0001,       # MOUSEEVENTF_MOVE
        int(dx),
        int(dy),
        0,
        0,
    )


def _get_network_editor() -> hou.NetworkEditor | None:
    for pane in hou.ui.paneTabs():
        if isinstance(pane, hou.NetworkEditor) and pane.isUnderCursor():
            return pane
    # fallback: first visible network editor
    for pane in hou.ui.paneTabs():
        if isinstance(pane, hou.NetworkEditor):
            return pane
    return None


def _shoot() -> None:
    import time
    global _last_shot
    now = time.monotonic()
    if now - _last_shot < 60.0 / RPM:
        return
    _last_shot = now

    editor = _get_network_editor()
    if editor is None:
        return

    parent = editor.pwd()
    if parent is None:
        return

    pos = editor.cursorPosition()
    try:
        node = parent.createNode(_node_type)
        node.setPosition(pos)
        node.setSelected(True, clear_all_selected=True)
        physics.explode(pos, parent)
    except hou.OperationFailed as e:
        print(f"[hotas] createNode failed: {e}")


def _poll() -> None:
    global _joystick, _held_prev
    if _joystick is None:
        return

    x, y, held = _joystick.poll()

    if x != 0.0 or y != 0.0:
        _move_mouse(x * SENSITIVITY, (-y if INVERT_Y else y) * SENSITIVITY)

    if held:
        _shoot()

    physics.tick()


def start(node_type: str = "null") -> None:
    """Start joystick input. Call from a Houdini shelf button."""
    global _joystick, _node_type

    if _joystick is not None:
        print("[hotas] Already running. Call stop() first.")
        return

    _node_type = node_type
    from houdini_hotas_control import config, node_sizer
    config.load()
    _joystick = VKBJoystick()
    _joystick.open()
    hou.ui.addEventLoopCallback(_poll)
    try:
        node_sizer.start()
    except Exception as e:
        print(f"[hotas] Throttle not started: {e}")
    print(f"[hotas] Started. Shooting '{node_type}' nodes. Call throw.stop() to quit.")


def stop() -> None:
    """Stop joystick input and release HID device."""
    global _joystick

    try:
        hou.ui.removeEventLoopCallback(_poll)
    except Exception:
        pass

    if _joystick is not None:
        _joystick.close()
        _joystick = None

    physics.clear()

    from houdini_hotas_control import node_sizer
    node_sizer.stop()
    print("[hotas] Stopped.")
