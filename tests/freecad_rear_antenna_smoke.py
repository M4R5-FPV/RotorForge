import sys,json,os,traceback
from pathlib import Path
import tempfile
root=Path(__file__).resolve().parents[1];base=Path(tempfile.mkdtemp(prefix='rotorforge-seat-'));sys.path.insert(0,str(root))
import freecad
freecad.__path__.insert(0,str(root/'freecad'))
import FreeCAD as App,Part
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.geometry import build_shapes
from freecad.rotorforge.antenna_layout import antenna_layout,antenna_standoff_bore
from freecad.rotorforge.mount_bands import rear_guard_band
results=[]
def save(r):
 results.append(r);(base/'cad.json').write_text(json.dumps(results,indent=2))
for plates in ('2 plates','3 plates'):
 for fit in ('Plate-edge wrap','Between plates'):
  for tilt in (0.,60.,90.):
   p=replace(Parameters(),PlateDesign=plates,FlexRearAntenna=True,FlexSideGuards=True,FlexGuardFitMode=fit,FlexAntennaTilt=tilt,FlexAntennaCount='2 antennas',FlexAntennaGripHeight=12.,FlexAntennaStandoffBore=6.2)
   try:
    s=build_shapes(p);mount=s['RearAntennaMount'];a=antenna_layout(p)
    assert mount.isValid() and len(mount.Solids)==1
    assert abs(a['z0']-rear_guard_band(p)[1])<1e-7
    for role in ('ElectronicsGuardLeft','ElectronicsGuardRight'):
     assert mount.common(s[role]).Volume<1e-6
     assert mount.distToShape(s[role])[0]<1e-6
    for stand in a['pair']:
     x,y=stand['point'];probe=Part.makeCylinder(antenna_standoff_bore(p)/2-.001,a['height']-.002,App.Vector(x,y,a['z0']+.001));assert mount.common(probe).Volume<1e-6
    save(dict(case=[plates,fit,tilt],ok=True))
    if plates=='3 plates' and fit=='Between plates' and tilt==60:
     mesh={}
     for role in ('RearAntennaMount','ElectronicsGuardLeft','ElectronicsGuardRight','Standoffs'):
      vs,fs=s[role].tessellate(.18);mesh[role]=dict(vertices=[list(v) for v in vs],faces=fs)
     (base/'assembly_mesh.json').write_text(json.dumps(mesh))
   except Exception:save(dict(case=[plates,fit,tilt],ok=False,error=traceback.format_exc()))
print('DONE',flush=True);os._exit(0 if len(results)==12 and all(r.get('ok') for r in results) else 1)
