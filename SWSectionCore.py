"""
SWSectionCore.py
================
Core engine that manages Coin3D SoClipPlane nodes in the active FreeCAD 3D view.

Public interface
----------------
ENGINE : SectionEngine   – singleton used by all commands and the panel
"""

import FreeCAD as App
import FreeCADGui as Gui
from pivy import coin


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _active_view():
    doc = Gui.ActiveDocument
    return doc.ActiveView if doc else None


def _scene():
    v = _active_view()
    return v.getSceneGraph() if v else None


def _remove_all_clip_planes(sg):
    """Strip every SoClipPlane node from the scene graph root."""
    i = 0
    while i < sg.getNumChildren():
        if isinstance(sg.getChild(i), coin.SoClipPlane):
            sg.removeChild(i)
        else:
            i += 1


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class SectionEngine:
    """
    Singleton that owns a single SoClipPlane inserted at index 0 of the
    active 3-D view's scene graph.

    State
    -----
    active   : bool            – whether a clip plane is currently live
    base     : App.Vector      – last applied origin point
    normal   : App.Vector      – last applied normal (unit vector)
    offset   : float           – current additional offset (mm) along normal
    """

    def __init__(self):
        self.active = False
        self.base   = App.Vector(0, 0, 0)
        self.normal = App.Vector(0, 0, 1)
        self.offset = 0.0
        self._clip  = None          # current coin.SoClipPlane node

    # ------------------------------------------------------------------
    # Low-level scene helpers
    # ------------------------------------------------------------------

    def _insert_clip(self, base, normal, offset=0.0):
        """Create and insert a SoClipPlane into the scene graph."""
        sg = _scene()
        if sg is None:
            App.Console.PrintError("SWSectionWorkbench: no active 3-D view\n")
            return False

        # Remove any stale clip planes first
        _remove_all_clip_planes(sg)

        # Build the Coin plane equation:  n · x + d = 0  where d = -(n · p)
        # Points on the *positive-normal side* are kept visible.
        effective_base = base + normal * offset

        nx, ny, nz = normal.x, normal.y, normal.z
        d = -(effective_base.x * nx + effective_base.y * ny + effective_base.z * nz)

        sb_normal = coin.SbVec3f(nx, ny, nz)
        sb_plane  = coin.SbPlane(sb_normal, d)

        self._clip = coin.SoClipPlane()
        self._clip.plane.setValue(sb_plane)
        self._clip.on.setValue(True)

        sg.insertChild(self._clip, 0)
        return True

    def _redraw(self):
        v = _active_view()
        if v:
            v.redraw()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def apply(self, base, normal):
        """
        Activate a section cut at *base* with outward direction *normal*.
        Any previous clip plane is replaced.
        """
        # Normalise
        length = normal.Length
        if length < 1e-10:
            App.Console.PrintError("SWSectionWorkbench: degenerate normal vector\n")
            return

        unit_normal = normal / length
        self.base   = base
        self.normal = unit_normal
        self.offset = 0.0

        if self._insert_clip(base, unit_normal, 0.0):
            self.active = True
            self._redraw()
            App.Console.PrintMessage(
                f"SWSection: section ON  base=({base.x:.2f},{base.y:.2f},{base.z:.2f})"
                f"  normal=({unit_normal.x:.3f},{unit_normal.y:.3f},{unit_normal.z:.3f})\n"
            )

    def remove(self):
        """Deactivate the section cut and restore the full view."""
        sg = _scene()
        if sg is not None:
            _remove_all_clip_planes(sg)
        self._clip  = None
        self.active = False
        self._redraw()
        App.Console.PrintMessage("SWSection: section OFF\n")

    def flip(self):
        """Reverse the clipping direction (flip the normal)."""
        if not self.active:
            App.Console.PrintMessage("SWSection: no active section to flip\n")
            return
        self.normal = self.normal * -1.0
        self._insert_clip(self.base, self.normal, self.offset)
        self._redraw()
        App.Console.PrintMessage("SWSection: normal flipped\n")

    def set_offset(self, offset_mm):
        """
        Translate the clip plane *along* the normal by *offset_mm* millimetres
        relative to the original base point.
        """
        if not self.active:
            return
        self.offset = offset_mm
        self._insert_clip(self.base, self.normal, offset_mm)
        self._redraw()

    def apply_from_3points(self, p1, p2, p3):
        """
        Compute a plane through three App.Vector points and activate it.
        The normal is (p2-p1) × (p3-p1).
        """
        v1 = p2 - p1
        v2 = p3 - p1
        normal = v1.cross(v2)
        if normal.Length < 1e-10:
            App.Console.PrintError("SWSectionWorkbench: the three points are collinear\n")
            return
        self.apply(p1, normal)


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------
ENGINE = SectionEngine()