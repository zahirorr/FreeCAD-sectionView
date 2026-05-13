"""
SWSectionPanel.py
=================
Qt task panel shown inside FreeCAD's Task panel area when the user opens the
"Section Offset" tool.  Provides:

 * a slider + spin-box for translating the clip plane along its normal
 * a "Flip Normal" button
 * a "Remove Section" button
 * live feedback (no Apply button needed)
"""

import os
import FreeCAD as App
import FreeCADGui as Gui

# Qt is shipped with FreeCAD; import via PySide2/PySide (whichever is present)
try:
    from PySide2 import QtCore, QtWidgets
except ImportError:
    from PySide import QtCore, QtGui as QtWidgets   # older FreeCAD builds

from SWSectionCore import ENGINE


_SLIDER_SCALE = 10.0   # slider integer units per mm


class SWSectionOffsetPanel(QtWidgets.QWidget):
    """Widget embedded in FreeCAD's task panel."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
        self._refresh_state()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(6, 6, 6, 6)

        # ---- Status label ----
        self.lbl_status = QtWidgets.QLabel("No active section")
        self.lbl_status.setAlignment(QtCore.Qt.AlignCenter)
        font = self.lbl_status.font()
        font.setBold(True)
        self.lbl_status.setFont(font)
        layout.addWidget(self.lbl_status)

        layout.addWidget(_separator())

        # ---- Offset controls ----
        off_group = QtWidgets.QGroupBox("Offset along normal (mm)")
        off_layout = QtWidgets.QVBoxLayout(off_group)

        slider_row = QtWidgets.QHBoxLayout()
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setRange(-5000, 5000)       # ±500 mm at scale 10
        self.slider.setValue(0)
        self.slider.setTickInterval(int(10 * _SLIDER_SCALE))
        self.slider.setTickPosition(QtWidgets.QSlider.TicksBelow)

        self.spin = QtWidgets.QDoubleSpinBox()
        self.spin.setRange(-500.0, 500.0)
        self.spin.setSingleStep(1.0)
        self.spin.setDecimals(1)
        self.spin.setSuffix(" mm")
        self.spin.setValue(0.0)
        self.spin.setFixedWidth(90)

        slider_row.addWidget(self.slider)
        slider_row.addWidget(self.spin)
        off_layout.addLayout(slider_row)

        btn_reset = QtWidgets.QPushButton("Reset offset")
        btn_reset.setToolTip("Bring section plane back to its original position")
        off_layout.addWidget(btn_reset)

        layout.addWidget(off_group)

        # ---- Action buttons ----
        layout.addWidget(_separator())

        self.btn_flip = QtWidgets.QPushButton("⇄  Flip Normal")
        self.btn_flip.setToolTip("Reverse the clipping direction")
        self.btn_flip.setMinimumHeight(32)
        layout.addWidget(self.btn_flip)

        self.btn_off = QtWidgets.QPushButton("✕  Remove Section")
        self.btn_off.setToolTip("Deactivate the section and restore the full view")
        self.btn_off.setMinimumHeight(32)
        self.btn_off.setStyleSheet("background:#8b2020; color:white; font-weight:bold;")
        layout.addWidget(self.btn_off)

        layout.addStretch()

        # ---- Connect signals ----
        self.slider.valueChanged.connect(self._on_slider)
        self.spin.valueChanged.connect(self._on_spin)
        btn_reset.clicked.connect(self._on_reset)
        self.btn_flip.clicked.connect(self._on_flip)
        self.btn_off.clicked.connect(self._on_remove)

    # ------------------------------------------------------------------
    # Signal handlers
    # ------------------------------------------------------------------

    def _on_slider(self, value):
        mm = value / _SLIDER_SCALE
        self.spin.blockSignals(True)
        self.spin.setValue(mm)
        self.spin.blockSignals(False)
        ENGINE.set_offset(mm)

    def _on_spin(self, mm):
        self.slider.blockSignals(True)
        self.slider.setValue(int(mm * _SLIDER_SCALE))
        self.slider.blockSignals(False)
        ENGINE.set_offset(mm)

    def _on_reset(self):
        self.slider.blockSignals(True)
        self.spin.blockSignals(False)
        self.slider.setValue(0)
        self.spin.setValue(0.0)
        self.slider.blockSignals(False)
        self.spin.blockSignals(False)
        ENGINE.set_offset(0.0)

    def _on_flip(self):
        ENGINE.flip()
        # After flip, slider offset is still valid in the new direction
        ENGINE.set_offset(self.spin.value())

    def _on_remove(self):
        ENGINE.remove()
        self._on_reset()
        self._refresh_state()
        # Close the task panel
        Gui.Control.closeDialog()

    # ------------------------------------------------------------------
    # State refresh
    # ------------------------------------------------------------------

    def _refresh_state(self):
        active = ENGINE.active
        if active:
            n = ENGINE.normal
            self.lbl_status.setText(
                f"Section ACTIVE\n"
                f"normal ({n.x:.3f}, {n.y:.3f}, {n.z:.3f})"
            )
            self.lbl_status.setStyleSheet("color:#00c8a0;")
        else:
            self.lbl_status.setText("No active section")
            self.lbl_status.setStyleSheet("color:#e05050;")
        self.btn_flip.setEnabled(active)
        self.btn_off.setEnabled(active)
        self.slider.setEnabled(active)
        self.spin.setEnabled(active)


# ------------------------------------------------------------------
# FreeCAD task-panel wrapper
# ------------------------------------------------------------------

class SWSectionOffsetTask:
    """Wrapper that satisfies FreeCAD's Gui.Control task-panel protocol."""

    def __init__(self):
        self.form = SWSectionOffsetPanel()

    def getMainWidget(self):
        return self.form

    def accept(self):
        Gui.Control.closeDialog()
        return True

    def reject(self):
        Gui.Control.closeDialog()
        return True


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _separator():
    line = QtWidgets.QFrame()
    line.setFrameShape(QtWidgets.QFrame.HLine)
    line.setFrameShadow(QtWidgets.QFrame.Sunken)
    return line
