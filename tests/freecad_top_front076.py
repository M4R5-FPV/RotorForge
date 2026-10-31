"""Top-front profiles, high-tilt camera fit, saved settings and export."""
import os,sys,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
import FreeCAD as App,Part
from freecad.rotorforge.parameters import Parameters,validate
from freecad.rotorforge.bottom_nose import TOP_FRONT_SHAPES,CAMERA_FRONT_SHAPES
from freecad.rotorforge import geometry as g,document as d
from freecad.rotorforge.exporters import export_package
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True);checks=[];fail=[]
try:
 for shape in TOP_FRONT_SHAPES:
  p=Parameters(TopFrontShape=shape,TopFrontRecessWidth=22.)
  s=g.profiled_plate(p,'TopPlate',50,-90,90,5,0,3)
  assert s.isValid() and len(s.Solids)==1,shape
  assert s.BoundBox.YMax<=90+1e-7 and s.Volume<=50*180*3
  checks.append('Native profile: '+shape)
 for shape in CAMERA_FRONT_SHAPES:
  for mode in ('2 plates','3 plates'):
   p=Parameters(FPVEnabled=True,PlateDesign=mode,TopFrontShape=shape,StandoffHeight=35.,CameraTilt=55.,CameraTiltMax=60.)
   assert not validate(p)[0],validate(p)[0]
   shapes=g.build_shapes(p)
   assert all(s.isValid() for s in shapes.values() if not s.isNull())
   for angle in (0.,30.,55.,60.):
    assert g.camera_envelope(p,angle).common(shapes['TopPlate']).Volume<1e-6,(shape,mode,angle)
   checks.append(mode+' '+shape+': complete assembly, camera sweep 0-60 degrees')
 p=Parameters(FPVEnabled=True,TopFrontShape='Camera swept recess',StandoffHeight=35.,CameraTilt=55.,CameraTiltMax=60.,TopFrontRecessWidth=24.,TopFrontDepth=18.,TopFrontSetback=4.)
 doc=App.newDocument();f=d.create_frame(p,doc)
 assert d.read_parameters(f)==p
 export_package(f,out/'export')
 doc.saveAs(str(out/'TopFront.FCStd'));App.closeDocument(doc.Name)
 doc=App.openDocument(str(out/'TopFront.FCStd'));f=doc.getObject('FrameParameters');q=d.read_parameters(f)
 assert q==p and not any(getattr(o.Proxy,'_shape_writes',0) for o in d.component_objects(f).values())
 App.closeDocument(doc.Name);checks.append('STEP/DXF/SVG export and saved settings restore without shape writes')
 g.build_for_update(p);q=replace(p,TopFrontDepth=19.);g.build_for_update(q);report=g.build_report(q)
 assert not any(n.startswith('Arm') for n in report['rebuilt']),report
 checks.append('Reused arms after top-front edit: '+repr(report['rebuilt']))
except Exception:fail.append(traceback.format_exc());traceback.print_exc()
(out/'top_front.json').write_text(json.dumps(dict(checks=checks,failures=fail),indent=2));print('RESULT',len(checks),fail,flush=True)
