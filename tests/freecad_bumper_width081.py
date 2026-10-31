"""Native regression: width, joined shoulders, fit and printable solids."""
import sys,os,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
import FreeCAD as App,Part,MeshPart
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.front_bumper import BUMPER_SHAPES,shoulder_hull
from freecad.rotorforge.bumper_geometry import front_bumper
from freecad.rotorforge import geometry as g
from freecad.rotorforge.flex_geometry import printable_flex
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True);checks=[];fail=[]
try:
 p=Parameters(FlexFrontBumper=True);parts=g.build_shapes(p);plate=parts['BottomPlate'];front=plate.BoundBox.YMax
 for style in BUMPER_SHAPES[1:]:
  for width in (8.,24.,0.,80.):
   q=replace(p,FlexBumperShape=style,FlexBumperWidth=width)
   shoe=front_bumper(q,{'BottomPlate':plate})
   assert shoe.isValid() and len(shoe.Solids)==1,(style,width)
   assert shoe.common(plate).Volume<1e-6,(style,width,'carbon fit')
   # At the shoulder the full commanded toe width is supported by sole.
   half=width/2 if width else (p.BodyWidth/2+p.FlexBumperWall+p.FlexBumperFit)
   section=Part.makeBox(2*half-.02,.05,.2,App.Vector(-half+.01,front+p.FlexBumperWall+p.FlexBumperFit-.06,-p.FlexBumperFit-p.FlexBumperSole+.1))
   assert section.cut(shoe).Volume<1e-6,(style,width,'shoulder gap')
   mesh=MeshPart.meshFromShape(Shape=printable_flex(shoe,'FrontBumper'),LinearDeflection=.08,AngularDeflection=.2,Relative=False)
   assert mesh.isSolid(),(style,width,'mesh')
   checks.append([style,width,'valid, connected, fit clear, shoulder joined, closed STL'])
 for nose in ('Rounded nose','V-notch','Twin lobes'):
  q=replace(p,BottomNoseShape=nose,FlexBumperWidth=70.)
  result=g.build_shapes(q);assert result['FrontBumper'].isValid();checks.append(['plate nose',nose])
 g.build_for_update(p);q=replace(p,FlexBumperWidth=70.);g.build_for_update(q);report=g.build_report(q)
 assert set(report['rebuilt'])<={'FrontBumper','FrameCGMarker'},report
 checks.append(['selective rebuild',report['rebuilt']])
 from freecad.rotorforge import document as d
 doc=App.newDocument('BumperWidth');frame=d.create_frame(q,doc);name=frame.Name
 file=out/'BumperWidth.FCStd';doc.saveAs(str(file));App.closeDocument(doc.Name)
 doc=App.openDocument(str(file));frame=doc.getObject(name)
 restored=d.read_parameters(frame);assert restored.FlexBumperWidth==70.
 assert 'FrontBumper' in g.build_shapes(restored)
 App.closeDocument(doc.Name);checks.append(['saved project width',70.])
except Exception:fail.append(traceback.format_exc());traceback.print_exc()
(out/'bumper_width.json').write_text(json.dumps(dict(checks=checks,failures=fail),indent=2));print(len(checks),fail,flush=True)
