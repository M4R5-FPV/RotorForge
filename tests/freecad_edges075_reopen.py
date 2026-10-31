"""Saved signed offsets and shaped rear selectors retain their values on restore."""
import sys,os,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App
from freecad.rotorforge import document as d
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);checks=[]
for mode in ('2','3'):
 doc=App.openDocument(str(out/('Edges_'+mode+'.FCStd')));f=doc.getObject('FrameParameters');p=d.read_parameters(f)
 assert p.CameraTabBottomFrontOffset==-.75 and p.CameraTabTopFrontOffset==-.5
 assert p.CameraTabBottomRearOffset==.5 and p.CameraTabTopRearOffset==.25
 assert p.TopRearShape=='Split tail' and p.TopRearDepth==2.
 assert f.getTypeIdOfProperty('CameraTabBottomFrontOffset')=='App::PropertyDistance'
 assert all(o.Shape.isValid() for o in d.component_objects(f).values() if not o.Shape.isNull())
 assert not any(getattr(o.Proxy,'_shape_writes',0) for o in d.component_objects(f).values())
 checks.append(mode+' plates: values and existing shapes restored without shape writes');App.closeDocument(doc.Name)
(out/'reopen_edges.json').write_text(json.dumps(dict(checks=checks,failures=[]),indent=2))
