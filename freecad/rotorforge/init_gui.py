"""FreeCAD namespaced GUI entry point. No geometry or Qt editor at startup."""
import FreeCADGui as Gui
from .workbench import RotorForgeWorkbench

if "RotorForgeWorkbench" not in Gui.listWorkbenches():
    Gui.addWorkbench(RotorForgeWorkbench())
