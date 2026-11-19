"""Workbench class in a normal module, independent of InitGui's exec namespace."""
from .paths import icon_path
import FreeCADGui as Gui
import FreeCAD as App


def _initialize_coin():
    """Load Pivy's SWIG bindings before RotorForge accesses scene nodes."""
    try:
        from pivy import coin  # noqa: F401
    except Exception as exc:
        App.Console.PrintWarning(
            f"RotorForge: Pivy/Coin3D initialization failed: {exc}\n"
        )
    else:
        App.Console.PrintMessage("RotorForge: Pivy/Coin3D initialized.\n")


class RotorForgeWorkbench(Gui.Workbench):
    MenuText = "RotorForge"
    ToolTip = "Drone Frame Editor — parametric frames and manufacturing profiles"
    Icon = icon_path()

    def Initialize(self):
        _initialize_coin()
        from .gui import register_commands
        commands = register_commands()
        self.appendToolbar("RotorForge", commands)
        self.appendMenu("RotorForge", commands)

    def GetClassName(self):
        return "Gui::PythonWorkbench"
