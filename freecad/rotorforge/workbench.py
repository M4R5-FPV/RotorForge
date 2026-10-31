"""Workbench class in a normal module, independent of InitGui's exec namespace."""
from .paths import icon_path
import FreeCADGui as Gui


class RotorForgeWorkbench(Gui.Workbench):
    MenuText = "RotorForge"
    ToolTip = "Drone Frame Editor — parametric frames and manufacturing profiles"
    Icon = icon_path()

    def Initialize(self):
        from .gui import register_commands
        commands = register_commands()
        self.appendToolbar("RotorForge", commands)
        self.appendMenu("RotorForge", commands)

    def GetClassName(self):
        return "Gui::PythonWorkbench"
