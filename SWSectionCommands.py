"""
SWSectionCommands.py
====================
All FreeCAD GUI commands for the SWSectionWorkbench.

Commands registered
-------------------
SW_SectionOn        – activate section from selection
SW_SectionOff       – deactivate section
SW_SectionToggle    – toggle section on/off
SW_SectionFlip      – flip the clipping direction
SW_SectionOffset    – open the offset/control task panel
SW_Section3Points   – activate section from 3 selected vertices
SW_SectionPlane     – create a PartDesign reference plane at the section position
"""

import os
import sys
import FreeCAD as App
import FreeCADGui as Gui

import SWSectionCore
import SWSectionPlane

ENGINE = SWSectionCore.ENGINE

# ---------------------------------------------------------------------------
# Resolve workbench directory (same fallback as InitGui.py)
# ---------------------------------------------------------------------------
try:
    _wb_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _wb_dir = ""
    for _p in sys.path:
        if (os.path.isfile(os.path.join(_p, "SWSectionCommands.py"))
                and os.path.basename(_p) == "SWSectionWorkbench"):
            _wb_dir = _p
            break
    if not _wb_dir:
        for _candidate in [
            os.path.join(App.getUserAppDataDir(), "Mod", "SWSectionWorkbench"),
            os.path.join(App.getHomePath(), "Mod", "SWSectionWorkbench"),
        ]:
            if os.path.isdir(_candidate):
                _wb_dir = _candidate
                break

# ---------------------------------------------------------------------------
# Helper: ask user to choose a standard plane when no geometry is selected
# ---------------------------------------------------------------------------
def _choose_standard_plane():
    """Show a small dialog asking the user to select Front, Right, or Top plane.
    Returns a tuple (base, normal) where base is App.Vector(0,0,0) and normal
    corresponds to the chosen orientation, or None if the user cancels.
    """
    try:
        from PySide2 import QtWidgets
    except ImportError:
        from PySide import QtGui as QtWidgets  # pragma: no cover

    dialog = QtWidgets.QDialog()
    dialog.setWindowTitle("Select Standard Plane")
    layout = QtWidgets.QVBoxLayout(dialog)
    label = QtWidgets.QLabel("No planar geometry selected. Choose a standard plane:")
    layout.addWidget(label)
    # Radio buttons
    rb_front = QtWidgets.QRadioButton("Front (Y‑axis)")
    rb_right = QtWidgets.QRadioButton("Right (X‑axis)")
    rb_top = QtWidgets.QRadioButton("Top (Z‑axis)")
    rb_front.setChecked(True)  # default
    layout.addWidget(rb_front)
    layout.addWidget(rb_right)
    layout.addWidget(rb_top)
    # OK / Cancel buttons
    btn_box = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
    layout.addWidget(btn_box)
    btn_box.accepted.connect(dialog.accept)
    btn_box.rejected.connect(dialog.reject)
    if dialog.exec_() != QtWidgets.QDialog.Accepted:
        return None
    # Determine normal based on selection
    if rb_front.isChecked():
        normal = App.Vector(0, 1, 0)  # front looks along -Y, normal pointing +Y
    elif rb_right.isChecked():
        normal = App.Vector(1, 0, 0)  # right side
    else:
        normal = App.Vector(0, 0, 1)  # top view normal
    base = App.Vector(0, 0, 0)
    return base, normal

_ICON_DIR = os.path.join(_wb_dir, "icons")


def _icon(name):
    """Return the absolute path for an icon SVG by base name (without extension)."""
    path = os.path.join(_ICON_DIR, name + ".svg")
    return path if os.path.isfile(path) else ""


def _get_plane():
    result = SWSectionPlane.get_plane_from_selection()
    if result is None:
        # Offer the standard plane choice dialog
        result = _choose_standard_plane()
        if result is None:
            App.Console.PrintWarning(
                "SWSectionWorkbench: no plane selected and user cancelled.\n"
            )
        else:
            App.Console.PrintMessage("SWSectionWorkbench: using standard plane selection.\n")
    return result


# ===========================================================================
# SW_SectionOn
# ===========================================================================

class CmdSectionOn:

    def GetResources(self):
        return {
            "MenuText": "Section ON",
            "Accel":    "Shift+S",
            "ToolTip": (
                "Activate a clipping section from the selected face or plane.\n"
                "Select a planar face, a datum plane, or any object with a "
                "Placement before clicking this button."
            ),
            "Pixmap": _icon("SW_SectionOn"),
        }

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def Activated(self):
        plane = _get_plane()
        if plane:
            base, normal = plane
            ENGINE.apply(base, normal)
            # Automatically open the offset panel so the user can adjust immediately
            from SWSectionPanel import SWSectionOffsetTask
            if Gui.Control.activeDialog():
                Gui.Control.closeDialog()
            Gui.Control.showDialog(SWSectionOffsetTask())


# ===========================================================================
# SW_SectionOff
# ===========================================================================

class CmdSectionOff:

    def GetResources(self):
        return {
            "MenuText": "Section OFF",
            "Accel":    "Shift+D",
            "ToolTip":  "Remove the active clipping plane and restore the full view.",
            "Pixmap":   _icon("SW_SectionOff"),
        }

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def Activated(self):
        ENGINE.remove()


# ===========================================================================
# SW_SectionToggle
# ===========================================================================

class CmdSectionToggle:

    def GetResources(self):
        return {
            "MenuText": "Toggle Section",
            "Accel":    "Shift+T",
            "ToolTip": (
                "Toggle the section cut on or off.\n"
                "When turning ON, the current selection is used to define the plane."
            ),
            "Pixmap": _icon("SW_SectionToggle"),
        }

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def Activated(self):
        if ENGINE.active:
            ENGINE.remove()
        else:
            plane = _get_plane()
            if plane:
                base, normal = plane
                ENGINE.apply(base, normal)
                # Automatically open the offset panel
                from SWSectionPanel import SWSectionOffsetTask
                if Gui.Control.activeDialog():
                    Gui.Control.closeDialog()
                Gui.Control.showDialog(SWSectionOffsetTask())


# ===========================================================================
# SW_SectionFlip
# ===========================================================================

class CmdSectionFlip:

    def GetResources(self):
        return {
            "MenuText": "Flip Section Normal",
            "Accel":    "Shift+F",
            "ToolTip": (
                "Reverse the clipping direction.\n"
                "Useful when the wrong half of the model is hidden."
            ),
            "Pixmap": _icon("SW_SectionFlip"),
        }

    def IsActive(self):
        return ENGINE.active

    def Activated(self):
        ENGINE.flip()


# ===========================================================================
# SW_SectionOffset
# ===========================================================================

class CmdSectionOffset:

    def GetResources(self):
        return {
            "MenuText": "Section Offset / Controls",
            "Accel":    "Shift+O",
            "ToolTip": (
                "Open the section control panel.\n"
                "Lets you slide the section plane along its normal, flip it, "
                "or remove it."
            ),
            "Pixmap": _icon("SW_SectionOffset"),
        }

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def Activated(self):
        from SWSectionPanel import SWSectionOffsetTask
        # Close any existing task panel first
        if Gui.Control.activeDialog():
            Gui.Control.closeDialog()
        Gui.Control.showDialog(SWSectionOffsetTask())


# ===========================================================================
# SW_Section3Points
# ===========================================================================

class CmdSection3Points:

    def GetResources(self):
        return {
            "MenuText": "Section from 3 Points",
            "Accel":    "Shift+3",
            "ToolTip": (
                "Define a section plane through 3 selected vertices.\n"
                "Select exactly 3 vertices (use Ctrl+Click) then click this button."
            ),
            "Pixmap": _icon("SW_Section3Points"),
        }

    def IsActive(self):
        return Gui.ActiveDocument is not None

    def Activated(self):
        pts = SWSectionPlane.get_3_vertices()
        if pts is None:
            App.Console.PrintWarning(
                "SWSectionWorkbench: please select exactly 3 vertices "
                "(Ctrl+Click each vertex) to define the section plane.\n"
            )
            return
        ENGINE.apply_from_3points(pts[0], pts[1], pts[2])


# ===========================================================================
# SW_SectionPlane  (datum plane creator)
# ===========================================================================

class CmdSectionPlane:

    def GetResources(self):
        return {
            "MenuText": "Create Datum Plane at Section",
            "ToolTip": (
                "Insert a PartDesign reference plane at the current section position.\n"
                "The plane is added to the active Body or the active document."
            ),
            "Pixmap": _icon("SW_SectionPlane"),
        }

    def IsActive(self):
        return ENGINE.active and App.ActiveDocument is not None

    def Activated(self):
        if not ENGINE.active:
            App.Console.PrintWarning("SWSectionWorkbench: activate a section first.\n")
            return

        doc  = App.ActiveDocument
        base = ENGINE.base + ENGINE.normal * ENGINE.offset
        norm = ENGINE.normal

        # Build a placement: Z-axis along the section normal
        rot = App.Rotation(App.Vector(0, 0, 1), norm)
        pl  = App.Placement(base, rot)

        # Try to add inside the active PartDesign Body, else add to document
        try:
            import PartDesignGui
            body = PartDesignGui.getActivePart()
            if body:
                plane = body.newObject("PartDesign::Plane", "SectionPlane")
                plane.Placement = pl
                doc.recompute()
                App.Console.PrintMessage("SWSection: datum plane added to Body.\n")
                return
        except Exception:
            pass

        # Fallback: plain Part::Plane in the document
        plane = doc.addObject("Part::Plane", "SectionPlane")
        plane.Placement = pl
        doc.recompute()
        App.Console.PrintMessage("SWSection: Part::Plane added to document.\n")