import sys,os,json,traceback,time
from pathlib import Path
import tempfile
base=Path(tempfile.mkdtemp(prefix='rotorforge-hook097-'));root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
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
out=[]
for style in ('Curved','Triangle','Rectangle'):
 for offset in (.5,8.,20.):
  for width in (2.,4.,8.):
   p=replace(Parameters(),FlexELRSEnabled=True,FlexSideGuards=True,FlexELRSBarShape=style,FlexELRSHookReach=offset,FlexELRSHookWidth=width)
   try:
    s=build_shapes(p);m=s['ELRSAntennaMount'];a=elrs_layout(p);size=a['support_size'];bottom=a['z0']+(a['height']-size)/2
    assert m.isValid() and len(m.Solids)==1
    for x,y,z in a['hooks']:
     # The whole rounded-square connector must remain present at the hook face,
     # not just a small rounded tip. Probe both sides of the outer tangent.
     for dy in (-.1,.1):
      slab=Part.makeBox(size,.02,size,App.Vector(x-size/2,y+a['radius']+dy,bottom))
      assert m.common(slab).Volume/slab.Volume>.95,'Narrow hook connection'
     bore=Part.makeCylinder(p.FlexELRSAntennaDiameter/2-.01,width+.02,App.Vector(x-width/2-.01,y,z),App.Vector(1,0,0))
     assert m.common(bore).Volume<1e-6,'Blocked hook bore'
    out.append({'case':[style,offset,width],'ok':True})
   except Exception:out.append({'case':[style,offset,width],'ok':False,'error':traceback.format_exc()})
   (base/'joints.json').write_text(json.dumps(out,indent=2))
os._exit(0 if all(v['ok'] for v in out) else 1)
