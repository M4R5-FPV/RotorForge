import sys,json,os,traceback
from pathlib import Path
import tempfile
root=Path(__file__).resolve().parents[1];base=Path(tempfile.mkdtemp(prefix='rotorforge-export-'));sys.path.insert(0,str(root))
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
 results.append(r);(base/'extra.json').write_text(json.dumps(results,indent=2))

from freecad.rotorforge.document import create_frame,read_parameters
from freecad.rotorforge.flex_geometry import printable_flex
import MeshPart
try:
 for fit in ('Plate-edge wrap','Between plates'):
  for shape in ('Triangle','Rectangle'):
   for count in ('1 antenna','2 antennas'):
    p=replace(Parameters(),FlexRearAntenna=True,FlexSideGuards=True,FlexGuardFitMode=fit,FlexAntennaBarShape=shape,FlexAntennaConnector='SMA',FlexAntennaCount=count,FlexAntennaTilt=45.,FlexAntennaStandoffBore=6.4)
    s=build_shapes(p);mount=s['RearAntennaMount']
    assert mount.isValid() and len(mount.Solids)==1
    for role in ('ElectronicsGuardLeft','ElectronicsGuardRight'):
     assert mount.common(s[role]).Volume<1e-6
     assert mount.distToShape(s[role])[0]<1e-6
    save(dict(case=[fit,shape,count],ok=True))
 flat=printable_flex(mount,'RearAntennaMount');flat.exportStep(str(base/'mount.step'));MeshPart.meshFromShape(Shape=flat,LinearDeflection=.08,AngularDeflection=.2,Relative=False).write(str(base/'mount.stl'))
 doc=App.newDocument('SeatTest');create_frame(p,doc);doc.recompute();doc.saveAs(str(base/'SeatTest.FCStd'));App.closeDocument(doc.Name)
 doc=App.openDocument(str(base/'SeatTest.FCStd'));doc.recompute();q=read_parameters(doc.getObject('FrameParameters'))
 assert q.FlexAntennaTilt==45 and abs(q.FlexAntennaStandoffBore-6.4)<1e-7
 assert any(o.Shape.Volume>0 for o in doc.Objects if hasattr(o,'FrameRole') and o.FrameRole=='RearAntennaMount')
 save(dict(export_and_native_restore=True,ok=True))
except Exception:save(dict(error=traceback.format_exc(),ok=False))
os._exit(0 if len(results)==9 and all(r.get('ok') for r in results) else 1)
