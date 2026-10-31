"""Compatibility namespace for saved RotorForge documents before 0.38.

New integrations should import freecad.rotorforge. Only the document proxy
module is retained here because older FCStd files serialize that import path.
"""
from freecad.rotorforge import __version__
