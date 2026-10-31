"""RotorForge namespace entry point; safe in headless FreeCAD and plain Python.

FreeCAD discovers this package before importing init_gui in GUI sessions.
Keep geometry and Qt imports lazy so startup stays lightweight.
"""
from .version import __version__
