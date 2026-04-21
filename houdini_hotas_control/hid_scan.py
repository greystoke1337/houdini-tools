# Run outside Houdini to find HID devices and inspect report bytes.
# Usage: python.exe -m houdini_hotas_control.hid_scan  (from houdini-tools dir)
# Press Ctrl+C to stop.

import hid
import time

# Known devices to label
KNOWN = {
    (0x231D, 0x0200): "VKB Gladiator EVO R",
    (0x044F, 0x0404): "Thrustmaster Warthog Throttle",
    (0x044F, 0x0402): "Thrustmaster Warthog Joystick",
}


def list_devices():
    print("=== HID Devices ===")
    for d in hid.enumerate():
        vid, pid = d["vendor_id"], d["product_id"]
        label = KNOWN.get((vid, pid), "")
        tag = f"  *** {label} ***" if label else ""
        print(f"  VID={vid:#06x} PID={pid:#06x}  usage={d['usage_page']:#06x}/{d['usage']:#06x}  "
              f"path={d['path']}  {d['product_string']}{tag}")
    print()


def watch(vid: int, pid: int, seconds: int = 30):
    label = KNOWN.get((vid, pid), f"VID={vid:#06x} PID={pid:#06x}")
    print(f"Watching: {label}  (move throttle / press buttons for {seconds}s)")
    print("Format: [report_id]  b00 b01 b02 ... (changing bytes marked with *)\n")

    dev = hid.device()
    dev.open(vid, pid)
    dev.set_nonblocking(True)

    baseline = {}
    t_end = time.monotonic() + seconds
    last_print = {}

    try:
        while time.monotonic() < t_end:
            report = dev.read(64)
            if not report:
                time.sleep(0.005)
                continue

            rid = report[0]
            data = list(report)
            prev = baseline.get(rid)

            if prev != data:
                changed = {i for i, (a, b) in enumerate(zip(data, prev or data)) if a != b}
                parts = []
                for i, v in enumerate(data):
                    s = f"{v:3d}"
                    parts.append(f"*{s}*" if i in changed else f" {s} ")
                line = f"[{rid:2d}]  " + " ".join(parts[:24])
                key = (rid, tuple(data))
                if key != last_print.get(rid):
                    print(line)
                    last_print[rid] = key
                baseline[rid] = data

    except KeyboardInterrupt:
        pass
    finally:
        dev.close()
    print("\nDone.")


if __name__ == "__main__":
    list_devices()

    # Auto-select Warthog throttle if present, else ask
    target = None
    for d in hid.enumerate():
        vid, pid = d["vendor_id"], d["product_id"]
        if (vid, pid) == (0x044F, 0x0404):
            target = (vid, pid)
            break

    if target is None:
        print("Warthog throttle not found. Enter VID and PID (hex, e.g. 044f 0404):")
        vid_s = input("VID> ").strip()
        pid_s = input("PID> ").strip()
        target = (int(vid_s, 16), int(pid_s, 16))

    watch(target[0], target[1], seconds=60)
