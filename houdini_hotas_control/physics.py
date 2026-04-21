"""
Per-node velocity physics for the Houdini network editor.

All coordinates are in network space (same as node.position()).
"""

import hou

DAMPING = 0.88          # velocity multiplier per tick
EXPLOSION_RADIUS = 6.0  # network units
EXPLOSION_FORCE = 10.0  # initial velocity magnitude at radius=0
STOP_THRESHOLD = 0.002  # velocity below this -> remove from sim

# node_path -> [vx, vy]
_velocities: dict[str, list[float]] = {}


def explode(origin: hou.Vector2, parent: hou.Node) -> None:
    """Blast all nodes in parent network away from origin."""
    for node in parent.children():
        pos = node.position()
        dx = pos[0] - origin[0]
        dy = pos[1] - origin[1]
        dist = (dx * dx + dy * dy) ** 0.5
        if dist < 0.001:
            dist = 0.001
        if dist > EXPLOSION_RADIUS:
            continue
        force = EXPLOSION_FORCE * (1.0 - dist / EXPLOSION_RADIUS)
        path = node.path()
        if path not in _velocities:
            _velocities[path] = [0.0, 0.0]
        _velocities[path][0] += (dx / dist) * force
        _velocities[path][1] += (dy / dist) * force


def tick() -> None:
    """Advance physics one step. Call every event loop tick."""
    if not _velocities:
        return

    dead = []
    for path, vel in _velocities.items():
        try:
            node = hou.node(path)
            if node is None:
                dead.append(path)
                continue
            pos = node.position()
            node.setPosition(hou.Vector2(pos[0] + vel[0], pos[1] + vel[1]))
            vel[0] *= DAMPING
            vel[1] *= DAMPING
            if abs(vel[0]) < STOP_THRESHOLD and abs(vel[1]) < STOP_THRESHOLD:
                dead.append(path)
        except Exception:
            dead.append(path)

    for path in dead:
        _velocities.pop(path, None)


def clear() -> None:
    _velocities.clear()
