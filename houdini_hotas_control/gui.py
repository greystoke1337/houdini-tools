"""
Floating tuning panel for Houdini HOTAS Control.
Call gui.show() from a Houdini shelf button.
"""

try:
    from PySide6 import QtWidgets, QtCore
except ImportError:
    from PySide2 import QtWidgets, QtCore

from houdini_hotas_control import physics, throw, node_sizer, config

_panel = None


class _Slider(QtWidgets.QWidget):
    def __init__(self, name, module, min_v, max_v, step, parent=None):
        super().__init__(parent)
        self._module = module
        self._name = name
        self._step = step

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        scale = 1.0 / step
        self._slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self._slider.setRange(round(min_v * scale), round(max_v * scale))
        self._slider.setValue(round(getattr(module, name) * scale))
        self._slider.setMinimumWidth(180)

        self._label = QtWidgets.QLabel()
        self._label.setMinimumWidth(46)
        self._label.setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        self._refresh_label()

        self._slider.valueChanged.connect(self._on_change)
        layout.addWidget(self._slider)
        layout.addWidget(self._label)

    def _on_change(self, int_val):
        value = int_val * self._step
        setattr(self._module, self._name, value)
        self._refresh_label()
        config.save()

    def _refresh_label(self):
        value = getattr(self._module, self._name)
        self._label.setText(f"{value:.3f}")


class PhysicsPanel(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent, QtCore.Qt.Tool)
        self.setWindowTitle("Houdini HOTAS Control")
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, False)

        form = QtWidgets.QFormLayout(self)
        form.setLabelAlignment(QtCore.Qt.AlignRight)

        params = [
            # label,              module,      attr,               min,    max,   step
            ("Sensitivity",       throw,       "SENSITIVITY",       1.0,  100.0,  0.5),
            ("RPM",               throw,       "RPM",              30.0, 1200.0, 10.0),
            ("Explosion Force",   physics,     "EXPLOSION_FORCE",   0.5,   50.0,  0.5),
            ("Explosion Radius",  physics,     "EXPLOSION_RADIUS",  0.5,   30.0,  0.5),
            ("Damping",           physics,     "DAMPING",           0.50,   0.99, 0.01),
            ("Scroll Speed",      node_sizer,  "SCROLL_SPEED",    200.0, 5000.0, 100.0),
        ]

        for label, module, attr, mn, mx, step in params:
            form.addRow(label, _Slider(attr, module, mn, mx, step))

        # Y-invert toggle
        self._invert_y = QtWidgets.QCheckBox()
        self._invert_y.setChecked(throw.INVERT_Y)
        self._invert_y.stateChanged.connect(
            lambda s: [setattr(throw, "INVERT_Y", bool(s)), config.save()]
        )
        form.addRow("Invert Y", self._invert_y)

        self.setFixedWidth(340)
        self.adjustSize()


def show():
    global _panel
    config.load()
    if _panel is None:
        _panel = PhysicsPanel()
    _panel.show()
    _panel.raise_()
