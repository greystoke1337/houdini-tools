"""
VKB Gladiator EVO R HID reader.

Report layout:
  ID 1:  axes + buttons
    byte[1-2]  -> X_raw = (byte[2]<<8) | byte[1], 12-bit, center=2048
    byte[3-4]  -> Y_raw = (byte[4]<<8) | byte[3], 12-bit, center=2048
    byte[17]   -> button bitmask; trigger = bit 0 (& 0x01)
  ID 12: button event (sent on state change)
    byte[2]    -> button bitmask; trigger = bit 1 (& 0x02)
"""

import hid

VKB_VID = 0x231D
VKB_PID = 0x0200

_AXIS_CENTER = 2048
_AXIS_RANGE = 2048.0
_DEADZONE = 0.25
_SMOOTH = 0.4   # EMA alpha: 1.0 = no smoothing, lower = more smoothing


def _normalize(raw):
    v = (raw - _AXIS_CENTER) / _AXIS_RANGE
    v = max(-1.0, min(1.0, v))
    if abs(v) < _DEADZONE:
        return 0.0
    sign = 1.0 if v > 0 else -1.0
    return sign * (abs(v) - _DEADZONE) / (1.0 - _DEADZONE)


class VKBJoystick:
    def __init__(self):
        self._dev = None
        self._x = 0.0
        self._y = 0.0
        self._trigger_held = False

    def open(self):
        self._dev = hid.device()
        self._dev.open(VKB_VID, VKB_PID)
        self._dev.set_nonblocking(True)

    def close(self):
        if self._dev:
            self._dev.close()
            self._dev = None

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    def poll(self):
        """Drain HID buffer. Returns (x, y, trigger_held).

        x/y are normalized -1.0 to 1.0 with deadzone and smoothing applied.
        trigger_held is True while trigger physically pressed.
        """
        if not self._dev:
            return 0.0, 0.0, False

        target_x = None
        target_y = None
        report = self._dev.read(64)
        while report:
            if report[0] == 1 and len(report) >= 18:
                target_x = _normalize((report[2] << 8) | report[1])
                target_y = _normalize((report[4] << 8) | report[3])
                self._trigger_held = bool(report[17] & 0x01)
            elif report[0] == 12 and len(report) >= 3:
                self._trigger_held = bool(report[2] & 0x02)
            report = self._dev.read(64)

        if target_x is not None:
            self._x += (target_x - self._x) * _SMOOTH
            self._y += (target_y - self._y) * _SMOOTH

        return self._x, self._y, self._trigger_held
