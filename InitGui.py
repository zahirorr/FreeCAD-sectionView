"""
InitGui.py
==========
FreeCAD GUI initialisation for the SWSectionWorkbench.

Registers all commands and creates the toolbar + menu.
"""

import os
import sys
import FreeCADGui as Gui
import FreeCAD as App

# ---------------------------------------------------------------------------
# Determine the workbench directory robustly.
# __file__ is NOT defined in all FreeCAD embedded-Python contexts, so we use
# a fallback chain instead of relying on it directly.
# ---------------------------------------------------------------------------
try:
    _wb_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # Search sys.path for the folder that contains this file
    _wb_dir = ""
    for _p in sys.path:
        if (os.path.isfile(os.path.join(_p, "InitGui.py"))
                and os.path.basename(_p) == "SWSectionWorkbench"):
            _wb_dir = _p
            break
    if not _wb_dir:
        # Last resort: look next to the FreeCAD user-data Mod folder
        for _candidate in [
            os.path.join(App.getUserAppDataDir(), "Mod", "SWSectionWorkbench"),
            os.path.join(App.getHomePath(), "Mod", "SWSectionWorkbench"),
        ]:
            if os.path.isdir(_candidate):
                _wb_dir = _candidate
                break

# Make sure Python can import every module in this folder
if _wb_dir and _wb_dir not in sys.path:
    sys.path.insert(0, _wb_dir)



# ---------------------------------------------------------------------------
# Workbench definition
# ---------------------------------------------------------------------------

class SWSectionWorkbench(Gui.Workbench):

    # Workbench identity shown in the workbench selector drop-down
    MenuText = "SW Section"
    ToolTip  = (
        "Interactive cross-section visualisation workbench.\n"
        "Clip the 3-D view using selected faces, datum planes, or 3 vertices."
    )
    Icon     = ""  # Set dynamically below to avoid embedded Python scope issues

    # All command names in display order
    _COMMANDS = [
        "SW_SectionOn",
        "SW_SectionOff",
        "SW_SectionToggle",
        "SW_SectionFlip",
        "SW_SectionOffset",
        "SW_Section3Points",
        "SW_SectionPlane",
    ]

    def Initialize(self):
        """Called once when the workbench is first loaded."""
        import SWSectionCommands

        # Register every command with the Gui system
        Gui.addCommand("SW_SectionOn",      SWSectionCommands.CmdSectionOn())
        Gui.addCommand("SW_SectionOff",     SWSectionCommands.CmdSectionOff())
        Gui.addCommand("SW_SectionToggle",  SWSectionCommands.CmdSectionToggle())
        Gui.addCommand("SW_SectionFlip",    SWSectionCommands.CmdSectionFlip())
        Gui.addCommand("SW_SectionOffset",  SWSectionCommands.CmdSectionOffset())
        Gui.addCommand("SW_Section3Points", SWSectionCommands.CmdSection3Points())
        Gui.addCommand("SW_SectionPlane",   SWSectionCommands.CmdSectionPlane())

        # Toolbar  (always visible while the workbench is active)
        self.appendToolbar("Section Tools", self._COMMANDS)

        # Main menu entry
        self.appendMenu("&Section", self._COMMANDS)

    def Activated(self):
        """Called every time the user switches to this workbench."""
        import FreeCAD as App
        App.Console.PrintMessage("SWSectionWorkbench: activated\n")

    def Deactivated(self):
        """Called when the user leaves this workbench."""
        # Optionally remove the clip plane so it doesn't stay when the
        # user switches away.  Comment out the next two lines if you
        # prefer the section to persist across workbench switches.
        # from SWSectionCore import ENGINE
        # ENGINE.remove()
        pass

    def GetClassName(self):
        return "Gui::PythonWorkbench"


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------
SWSectionWorkbench.Icon = os.path.join(_wb_dir, "icons", "SW_SectionOn.svg")
Gui.addWorkbench(SWSectionWorkbench())