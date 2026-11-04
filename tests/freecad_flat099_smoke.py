import sys,os,json,traceback,time
from pathlib import Path
import tempfile
base=Path(tempfile.mkdtemp(prefix='rotorforge-flat099-'));root=Path(__file__).resolve().parents[1];sys.path.insert(0,str(root))
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
os.environ['ROTORFORGE_DISABLE_DISK_CACHE']='1'
from freecad.rotorforge.antenna_geometry import rear_antenna_mount
out=[]
p=replace(Parameters(),FlexRearAntenna=True,FlexSideGuards=True)
inputs=build_shapes(p)
for connector in ('u.FL','MMCX'):
 for style in ('Closed tube','Side-entry clip'):
  for angle in (0.,30.,60.,90.):
   for count in ('1 antenna','2 antennas'):
    q=replace(p,FlexAntennaConnector=connector,FlexAntennaHolderStyle=style,FlexAntennaTilt=angle,FlexAntennaCount=count,FlexAntennaHolderOffset=8,FlexAntennaSocketLength=20)
    try:
     m=rear_antenna_mount(q,inputs);a=antenna_layout(q)
     assert m.isValid() and len(m.Solids)==1
     b=m.BoundBox;z=a['z0']
     below=Part.makeBox(b.XLength+2,b.YLength+2,100,App.Vector(b.XMin-1,b.YMin-1,z-100))
     assert m.common(below).Volume<1e-7
     vertices,_=m.tessellate(.05)
     assert abs(min(v.z for v in vertices)-z)<1e-6
     for holder in a['holders']:
      axis=App.Vector(*holder['axis']);start=App.Vector(*holder['start']);probe=Part.makeCylinder(a['bore']/2-.01,a['length'],start,axis)
      assert m.common(probe).Volume<1e-6
     out.append({'case':[connector,style,angle,count],'ok':True})
    except Exception:out.append({'case':[connector,style,angle,count],'ok':False,'error':traceback.format_exc()})
    (base/'checks.json').write_text(json.dumps(out,indent=2))
os._exit(0 if all(x['ok'] for x in out) else 1)
