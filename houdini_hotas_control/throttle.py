import hid

WARTHOG_VID = 0x044F
WARTHOG_PID = 0x0404

_AXIS_MAX = 16383.0


def _normalize(raw):
    return max(0.0, min(1.0, raw / _AXIS_MAX))


class WarthogThrottle:
    def __init__(self):
        self._dev = None
        self._value = 0.0

    def open(self):
        self._dev = hid.device()
        self._dev.open(WARTHOG_VID, WARTHOG_PID)
        self._dev.set_nonblocking(True)

    def close(self):
        if self._dev:
            self._dev.close()
            self._dev = None

    def poll(self):
        """Drain HID buffer. Returns throttle position 0.0 (min) to 1.0 (max)."""
        if not self._dev:
            return self._value
        report = self._dev.read(64)
        while report:
            if report[0] == 1 and len(report) >= 14:
                raw = (report[13] << 8) | report[12]
                self._value = _normalize(raw)
            report = self._dev.read(64)
        return self._value
