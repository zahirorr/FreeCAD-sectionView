"""
SWSectionPlane.py
=================
Utilities for extracting a (base, normal) plane definition from the current
FreeCAD selection.

Supported inputs
----------------
* A single planar **Face** on any Part / PartDesign shape
* A **datum plane** (PartDesign::Plane, Part::Plane)
* Any object that carries a **Placement** (used as XY-plane of that placement)
* Three **vertices** selected in sequence (delegated to SWSectionCore)
"""

import FreeCAD as App
import FreeCADGui as Gui


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_datum_plane(obj):
    """Return True for PartDesign::Plane / Part::Plane and similar."""
    type_id = obj.TypeId if hasattr(obj, "TypeId") else ""
    return "Plane" in type_id or "Datum" in type_id


def _placement_plane(obj):
    """Return (base, normal) from an object's Placement (Z-axis of placement)."""
    pl = obj.Placement
    base   = pl.Base
    normal = pl.Rotation.multVec(App.Vector(0, 0, 1))
    return base, normal


def _face_plane(face):
    """Return (base, normal) from a Part face, or None if not planar."""
    try:
        # Use the face's surface normal at the parameter midpoint
        u0, u1, v0, v1 = face.ParameterRange
        u_mid = (u0 + u1) / 2.0
        v_mid = (v0 + v1) / 2.0
        base   = face.CenterOfMass
        normal = face.normalAt(u_mid, v_mid)
        return base, normal
    except Exception:
        # Fallback: use first vertex and a rough normal
        if len(face.Vertexes) >= 1:
            return face.Vertexes[0].Point, App.Vector(0, 0, 1)
        return None


def _vertex_points(sel_ex_list):
    """
    Collect up to 3 vertex points from the selection.
    Returns a list of App.Vector (may be empty or fewer than 3).
    """
    points = []
    for sel_ex in sel_ex_list:
        for sub_obj in sel_ex.SubObjects:
            if hasattr(sub_obj, "Point"):       # vertex
                points.append(sub_obj.Point)
            if len(points) == 3:
                return points
    return points


# ---------------------------------------------------------------------------
# Main public function
# ---------------------------------------------------------------------------

def get_plane_from_selection():
    """
    Inspect the current FreeCAD selection and return (base, normal) if a
    valid plane can be derived, otherwise return None.

    Priority order
    --------------
    1. A selected face (planar surface)
    2. A datum / reference plane object
    3. Any object with a Placement (uses its local Z axis)
    4. Three selected vertices (caller must use ENGINE.apply_from_3points)
    """
    sel = Gui.Selection.getSelectionEx()
    if not sel:
        return None

    # ---- 1. Face selection -----------------------------------------------
    for sel_ex in sel:
        if sel_ex.HasSubObjects:
            for sub in sel_ex.SubObjects:
                try:
                    import Part
                    if isinstance(sub, Part.Face):
                        result = _face_plane(sub)
                        if result:
                            return result
                except ImportError:
                    pass
                # Generic fallback: object with normalAt
                if hasattr(sub, "normalAt"):
                    result = _face_plane(sub)
                    if result:
                        return result

    # ---- 2. Datum / reference plane object --------------------------------
    for sel_ex in sel:
        obj = sel_ex.Object
        if _is_datum_plane(obj) and hasattr(obj, "Placement"):
            return _placement_plane(obj)

    # ---- 3. Any object with a Placement -----------------------------------
    for sel_ex in sel:
        obj = sel_ex.Object
        if hasattr(obj, "Placement"):
            return _placement_plane(obj)

    return None


def get_3_vertices():
    """
    Return a list of exactly 3 App.Vector from selected vertices,
    or None if fewer than 3 vertices are selected.
    """
    sel = Gui.Selection.getSelectionEx()
    pts = _vertex_points(sel)
    return pts if len(pts) == 3 else None