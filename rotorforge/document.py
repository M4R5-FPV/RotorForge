"""Restore older FCStd proxy paths using the canonical namespaced classes."""
import importlib
import sys
sys.modules[__name__] = importlib.import_module("freecad.rotorforge.document")
