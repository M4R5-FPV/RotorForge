import sys,os,json,traceback,time
from pathlib import Path
import tempfile
base=Path(tempfile.mkdtemp(prefix='rotorforge-mount095-'));root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
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
from freecad.rotorforge.snap_channels import full_entry_tool,front_direction
from freecad.rotorforge.antenna_geometry import rear_antenna_mount
out=[]
def record(d):out.append(d);(base/'channels.json').write_text(json.dumps(out,indent=2))
for count in ('1 antenna','2 antennas'):
 for tilt in (0.,30.,60.,90.):
  for length in (6.,30.):
   p=replace(Parameters(),FlexRearAntenna=True,FlexSideGuards=True,FlexAntennaHolderStyle='Side-entry clip',FlexAntennaCount=count,FlexAntennaTilt=tilt,FlexAntennaSocketLength=length,FlexAntennaHolderOffset=8)
   try:
    s=build_shapes(p);m=s['RearAntennaMount'];assert m.isValid() and len(m.Solids)==1;a=antenna_layout(p)
    closed=rear_antenna_mount(replace(p,FlexAntennaHolderStyle='Closed tube'),s)
    removed=0.
    for holder in a['holders']:
     start=App.Vector(*holder['start']);axis=App.Vector(*holder['axis']);n=front_direction(axis);assert n.y>=-1e-8
     tool=full_entry_tool(Part.makeCompound([closed,m]),start,axis,a['bore'],a['radius'],p.FlexAntennaRetainingLip)
     assert overlap_volume(m,tool)<1e-6,'Blocked channel through support stock'
     removed+=closed.common(tool).Volume
     across=n.cross(axis);across.normalize();c=start+axis*(a['length']*.7)
     x=a['bore']/2-p.FlexAntennaRetainingLip+.1;y=math.sqrt((a['bore']/2+.2)**2-x*x)
     for sign in (-1,1):assert m.isInside(c+across*(sign*x)+n*y,1e-6,True),'Missing retaining lip'
    assert removed>0
    record({'vtx':[count,tilt,length],'ok':True})
   except Exception:record({'vtx':[count,tilt,length],'ok':False,'error':traceback.format_exc()})
for style in ('Curved','Triangle','Rectangle'):
 for offset in (0.,8.,20.):
  p=replace(Parameters(),FlexELRSEnabled=True,FlexRearAntenna=True,FlexSideGuards=True,FlexELRSBarShape=style,FlexELRSHookReach=offset,FlexELRSPassThroughDiameter=4)
  try:
   s=build_shapes(p);m=s['ELRSAntennaMount'];a=elrs_layout(p);b=elrs_layout(replace(p,FlexELRSHookReach=0))
   assert a['points']==b['points'] and a['bar_y']==b['bar_y'];assert abs(a['y']-(b['y']-offset))<1e-6
   probe=Part.makeCylinder(1.99,m.BoundBox.YLength+2,App.Vector(0,m.BoundBox.YMin-1,a['z']),App.Vector(0,1,0))
   assert overlap_volume(m,probe)<1e-6;assert m.isValid() and len(m.Solids)==1
   record({'elrs':[style,offset],'ok':True})
   if style=='Curved' and offset==8:
    meshes={}
    for role in ('ELRSAntennaMount','RearAntennaMount'):
     vs,fs=s[role].tessellate(.12);meshes[role]={'vertices':[list(v) for v in vs],'faces':fs}
    (base/'meshes.json').write_text(json.dumps(meshes))
  except Exception:record({'elrs':[style,offset],'ok':False,'error':traceback.format_exc()})
os._exit(0 if all(d['ok'] for d in out) else 1)
