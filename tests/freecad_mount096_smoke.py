import sys,os,json,traceback,time
from pathlib import Path
import tempfile
base=Path(tempfile.mkdtemp(prefix='rotorforge-mount096-'));root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
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
from freecad.rotorforge.antenna_geometry import rear_antenna_mount
out=[]
for hookwidth,height in ((2.,6.),(4.,6.),(8.,6.),(4.,10.)):
 p=replace(Parameters(),FlexELRSEnabled=True,FlexELRSHookReach=20,FlexELRSHookWidth=hookwidth,FlexELRSGripHeight=height,FlexSideGuards=True)
 try:
  s=build_shapes(p);a=elrs_layout(p);size=min(hookwidth,a['height']);x,y,z=a['hooks'][0];mid=(a['bar_y']+y+a['radius']+size/2-.5)/2
  section=s['ELRSAntennaMount'].common(Part.makeBox(size+1,.01,height+2,App.Vector(x-size/2-.5,mid,a['z0']-1)))
  assert abs(section.BoundBox.XLength-size)<1e-5
  assert abs(section.BoundBox.ZLength-size)<1e-5
  out.append({'section':[hookwidth,height],'ok':True})
 except Exception:out.append({'section':[hookwidth,height],'ok':False,'error':traceback.format_exc()})
p=replace(Parameters(),FlexRearAntenna=True,FlexAntennaHolderStyle='Side-entry clip',FlexAntennaCount='2 antennas',FlexAntennaHolderOffset=8)
s=build_shapes(p);m=s['RearAntennaMount'];closed=rear_antenna_mount(replace(p,FlexAntennaHolderStyle='Closed tube'),s)
assert m.cut(closed).Volume<1e-6,'Extra bracing remains'
out.append({'no_added_vtx_brace':True,'ok':True})
(base/'sections.json').write_text(json.dumps(out,indent=2));os._exit(0 if all(x['ok'] for x in out) else 1)
