import ctypes
import hou
from houdini_hotas_control.throttle import WarthogThrottle

# Scroll sensitivity: wheel delta units per full throttle travel
# Windows WHEEL_DELTA = 120 per notch; Houdini typically zooms on scroll
SCROLL_SPEED = 2400

_throttle: WarthogThrottle | None = None
_last_t: float = -1.0


def _scroll(delta: int) -> None:
    ctypes.windll.user32.mouse_event(0x0800, 0, 0, delta, 0)


def _poll() -> None:
    global _last_t
    if _throttle is None:
        return

    t = _throttle.poll()
    if _last_t < 0.0:
        _last_t = t
        return

    delta_t = t - _last_t
    if abs(delta_t) < 0.002:
        return
    _last_t = t

    scroll_delta = int(delta_t * SCROLL_SPEED)
    if scroll_delta == 0:
        return
    _scroll(scroll_delta)


def start() -> None:
    global _throttle
    if _throttle is not None:
        print("[node_sizer] Already running. Call stop() first.")
        return
    from houdini_hotas_control import config
    config.load()
    _throttle = WarthogThrottle()
    _throttle.open()
    hou.ui.addEventLoopCallback(_poll)
    print("[node_sizer] Started. Move throttle to zoom network editor.")


def stop() -> None:
    global _throttle, _last_t
    try:
        hou.ui.removeEventLoopCallback(_poll)
    except Exception:
        pass
    if _throttle is not None:
        _throttle.close()
        _throttle = None
    _last_t = -1.0
    print("[node_sizer] Stopped.")
