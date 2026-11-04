import sys,json,os,traceback
from pathlib import Path
import tempfile
base=Path(tempfile.mkdtemp(prefix='rotorforge-holder-'));root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import freecad
freecad.__path__.insert(0,str(root/'freecad'))
import FreeCAD as App,Part
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.geometry import build_shapes
from freecad.rotorforge.antenna_layout import antenna_layout
from freecad.rotorforge.antenna_geometry import rear_antenna_mount
results=[]
def save(r):
 results.append(r);(base/'cad.json').write_text(json.dumps(results,indent=2))
for plates in ('2 plates','3 plates'):
 for fit in ('Plate-edge wrap','Between plates'):
  for tilt in (0.,60.,90.):
   p=replace(Parameters(),PlateDesign=plates,FlexRearAntenna=True,FlexSideGuards=True,FlexGuardFitMode=fit,FlexAntennaTilt=tilt,FlexAntennaCount='2 antennas',FlexAntennaSocketLength=35.,FlexAntennaHolderOffset=12.)
   try:
    s=build_shapes(p);mount=s['RearAntennaMount'];a=antenna_layout(p);assert mount.isValid() and len(mount.Solids)==1
    if tilt>0:assert mount.BoundBox.ZMax>a['top']+5
    for role in ('BottomPlate','MidPlate','TopPlate','ElectronicsGuardLeft','ElectronicsGuardRight'):
     if not s[role].isNull():assert mount.common(s[role]).Volume<1e-6
    save(dict(case=[plates,fit,tilt],ok=True))
    if plates=='3 plates' and fit=='Between plates' and tilt==60:
     vs,fs=mount.tessellate(.15);(base/'mesh.json').write_text(json.dumps({'vertices':[list(v) for v in vs],'faces':fs}))
   except Exception:save(dict(case=[plates,fit,tilt],ok=False,error=traceback.format_exc()))
# Explicit actual-solid collision regression: a plate across a sleeve must reject.
try:
 p=replace(Parameters(),FlexRearAntenna=True,FlexAntennaSocketLength=35.,FlexAntennaHolderOffset=10.)
 s=build_shapes(p);h=antenna_layout(p)['holders'][0];x,y,z=h['centre']
 for role in ('BottomPlate','MidPlate'):
  inputs=dict(s);inputs[role]=s[role].fuse(Part.makeBox(12,12,1,App.Vector(x-6,y-6,z))) if not s[role].isNull() else Part.makeBox(12,12,1,App.Vector(x-6,y-6,z))
  try:rear_antenna_mount(p,inputs)
  except ValueError as e:assert role in str(e);save(dict(blocks=role,ok=True))
  else:raise AssertionError('Missed plate collision')
except Exception:save(dict(ok=False,error=traceback.format_exc()))
os._exit(0 if all(r['ok'] for r in results) else 1)
