import os,sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
import FreeCAD as App
from freecad.rotorforge import document as d,hardware_refs as hw
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT'])
doc=App.openDocument(str(out/'AutoHardware.FCStd'));frame=doc.getObject('FrameParameters');p=d.read_parameters(frame)
before={o.HardwareRole:o.Name for o in hw.objects(frame)}
q=replace(p,StackHeight=p.StackHeight+.2)
d.update_frame(frame,q)
assert {o.HardwareRole:o.Name for o in hw.objects(frame)}==before
assert hw.options(frame)['groups']==['Arm bolts','Stack hardware']
assert all(o.Shape.isValid() for o in hw.objects(frame))
assert not hw.settings(frame).ReferencesStale
(out/'hardware_reopen.json').write_text(json.dumps(dict(saved_settings_and_update=True,stable_objects=list(before)),indent=2))
App.closeDocument(doc.Name)
