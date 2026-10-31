"""Compatibility entry point for current width/reach pad regression checks."""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name('freecad_pad_reach_smoke.py')),run_name='__main__')
