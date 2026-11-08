"""Run inside FreeCAD's Python interpreter to verify the new 3D antenna visuals.

Usage (FreeCAD console):
    import runpy; runpy.run_path(r".../RotorForge/tests/freecad_antenna_reference0911_smoke.py")

Requires no GUI screenshots or document files; only native Part geometry and
portable rear mount layouts. Printing success is intentionally explicit.
"""
from dataclasses import replace
from pathlib import Path
import os, sys, traceback

ROOT=Path(__file__).resolve().parents[1] if '__file__' in globals() else Path.cwd()
sys.path.insert(0,str(ROOT))
import FreeCAD as App
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.antenna_layout import antenna_layout
from freecad.rotorforge.elrs_layout import elrs_layout
from freecad.rotorforge.antenna_reference_models import antenna_reference,reference_enabled
from freecad.rotorforge.antenna_preset_specs import VTX_PRESETS,ELRS_SPAN_PRESETS,elrs_spec
from freecad.rotorforge.geometry import REFERENCE_ROLES,physical_roles

checks=[]
for connector in ('u.FL','MMCX','SMA','RP-SMA'):
    for count in ('1 antenna','2 antennas'):
        p=replace(Parameters(),FlexRearAntenna=True,ShowVTXAntennaReference=True,
                  FlexAntennaConnector=connector,FlexAntennaCount=count,
                  FlexAntennaTilt=50.)
        shape,colors=antenna_reference(p,'VTXAntennaReference')
        assert shape.isValid() and len(shape.Faces)==len(colors) and shape.Volume>0
        assert len(antenna_layout(p)['holders'])==(2 if count=='2 antennas' else 1)
        assert reference_enabled(p,'VTXAntennaReference')
        checks.append(('vtx',connector,count))
for reach in (0.,12.,30.):
    for preset in ELRS_SPAN_PRESETS:
        p=replace(Parameters(),FlexELRSEnabled=True,ShowELRSTReference=True,
                  FlexELRSHookReach=reach,ELRSTReferencePreset=preset,
                  ELRSTReferenceSpan=85.)
        shape,colors=antenna_reference(p,'ELRSTReference')
        assert shape.isValid() and len(shape.Faces)==len(colors) and shape.Volume>0
        a=elrs_layout(p)
        assert abs(shape.BoundBox.YMin-(a['y']-max(p.FlexELRSAntennaDiameter/2.,1.75)))<.01
        assert abs(shape.BoundBox.XLength-elrs_spec(p)['span'])<.02
        checks.append(('elrs',reach,preset))
for preset in VTX_PRESETS:
    p=replace(Parameters(),FlexRearAntenna=True,ShowVTXAntennaReference=True,
              VTXAntennaReferencePreset=preset)
    shape,colors=antenna_reference(p,'VTXAntennaReference')
    assert shape.isValid() and len(shape.Faces)==len(colors) and shape.Volume>0
    checks.append(('vtx',preset))
assert {'VTXAntennaReference','ELRSTReference'}<=set(REFERENCE_ROLES)
assert {'VTXAntennaReference','ELRSTReference'}.isdisjoint(physical_roles(Parameters()))
print('RotorForge 0.90.13: antenna geometry smoke checks passed:',len(checks))
