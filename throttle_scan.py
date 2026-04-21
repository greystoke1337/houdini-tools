# Quick Warthog throttle axis scanner.
# Run this then sweep the throttle axis from min to max while it runs.
# Usage: python.exe throttle_scan.py

import hid, time

VID, PID = 0x044F, 0x0404

dev = hid.device()
dev.open(VID, PID)
dev.set_nonblocking(True)

print("Move throttle axis from MIN to MAX now. Running 15s...")
print()

mins = {}
maxs = {}
t_end = time.monotonic() + 15

while time.monotonic() < t_end:
    r = dev.read(64)
    if not r:
        time.sleep(0.005)
        continue
    for i, v in enumerate(r):
        if i not in mins:
            mins[i] = v
            maxs[i] = v
        else:
            mins[i] = min(mins[i], v)
            maxs[i] = max(maxs[i], v)

dev.close()

print("Byte  Min  Max  Range")
print("----  ---  ---  -----")
for i in sorted(mins):
    span = maxs[i] - mins[i]
    if span > 0:
        marker = " <--- AXIS?" if span > 50 else ""
        print(f"  {i:2d}  {mins[i]:3d}  {maxs[i]:3d}  {span:5d}{marker}")
