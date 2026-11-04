import sys,os,json,traceback,time
from pathlib import Path
import tempfile
base=Path(tempfile.mkdtemp(prefix='rotorforge-antenna094-'));root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
import freecad
freecad.__path__.insert(0,str(root/'freecad'))
import FreeCAD as App,Part
from dataclasses import replace
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.geometry import build_shapes,overlap_volume
from freecad.rotorforge.elrs_layout import elrs_layout
from freecad.rotorforge.antenna_layout import antenna_layout
from freecad.rotorforge.dependency_cache import COMPONENTS
results=[]
def save(x):
 results.append(x);(base/'cad.json').write_text(json.dumps(results,indent=2))
import math
from freecad.rotorforge.elrs_geometry import elrs_mount
from freecad.rotorforge.antenna_geometry import rear_antenna_mount
out=[]
def save_test(d):
 out.append(d);(base/'openings.json').write_text(json.dumps(out,indent=2))
for connector in ('u.FL','MMCX'):
 for count in ('1 antenna','2 antennas'):
  for tilt in (0.,60.,90.):
   p=replace(Parameters(),FlexRearAntenna=True,FlexSideGuards=True,FlexAntennaConnector=connector,FlexAntennaCount=count,FlexAntennaTilt=tilt,FlexAntennaSocketLength=25,FlexAntennaHolderOffset=12,FlexAntennaHolderStyle='Side-entry clip')
   try:
    s=build_shapes(p);a=antenna_layout(p);m=s['RearAntennaMount'];assert m.isValid() and len(m.Solids)==1
    # Probe the actual radial channel and the retained tube wall opposite it.
    for item in a['holders']:
     axis=App.Vector(*item['axis']);anchor=App.Vector(*item['anchor']);start=App.Vector(*item['start']);c=start+axis*(a['length']*.8)
     yaw=math.atan2(axis.x,-axis.y) if abs(axis.x)+abs(axis.y)>1e-8 else (math.pi/6 if anchor.x>0 else -math.pi/6 if anchor.x<0 else 0);sign=-1 if anchor.x<0 else 1;n=__import__('freecad.rotorforge.snap_channels',fromlist=['front_direction']).front_direction(axis)
     probe=Part.makeCylinder(.1,a['radius']+1,c,n);assert overlap_volume(m,probe)<1e-6
     assert m.isInside(c-n*(a['bore']/2+p.FlexAntennaSocketWall/2),1e-6,True)
    save_test({'case':[connector,count,tilt],'ok':True})
   except Exception:save_test({'case':[connector,count,tilt],'ok':False,'error':traceback.format_exc()})
for shape in ('Curved','Triangle','Rectangle'):
 for guards in (False,True):
  p=replace(Parameters(),FlexELRSEnabled=True,FlexSideGuards=guards,FlexELRSBarShape=shape,FlexELRSHeightOffset=1,FlexELRSHookSpacing=20,FlexELRSReach=28)
  try:
   s=build_shapes(p);m=s['ELRSAntennaMount'];a=elrs_layout(p);assert m.isValid() and len(m.Solids)==1
   for x,y,z in a['hooks']:
    assert overlap_volume(m,Part.makeCylinder(.1,a['radius']+1,App.Vector(x,y,z),App.Vector(0,0,1)))<1e-6
    assert m.isInside(App.Vector(x,y,z-p.FlexELRSAntennaDiameter/2-p.FlexELRSHookWall/2),1e-6,True)
   save_test({'elrs':[shape,guards],'ok':True})
  except Exception:save_test({'elrs':[shape,guards],'ok':False,'error':traceback.format_exc()})
# Place actual stock through a hook to prove collision checks remain active.
try:
 p=replace(Parameters(),FlexELRSEnabled=True);s=build_shapes(p);a=elrs_layout(p);x,y,z=a['hooks'][0]
 for role in ('BottomPlate','MidPlate'):
  inputs=dict(s);inputs[role]=Part.makeBox(40,80,2,App.Vector(-20,a['rear']-60,z-a['radius']+.2))
  try:elrs_mount(p,inputs)
  except ValueError as e:assert role in str(e);save_test({'collision':role,'ok':True})
  else:raise AssertionError('Missed plate collision')
except Exception:save_test({'collision':True,'ok':False,'error':traceback.format_exc()})
os._exit(0 if all(r['ok'] for r in out) else 1)
