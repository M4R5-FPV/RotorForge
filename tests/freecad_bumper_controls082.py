"""Native extreme toe features and independent retaining-lip reach."""
import sys,os,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
import MeshPart
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.front_bumper import BUMPER_SHAPES
from freecad.rotorforge.bumper_geometry import front_bumper
from freecad.rotorforge import geometry as g
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);checks=[];fail=[]
try:
 p=Parameters(FlexFrontBumper=True,FlexBumperWidth=70.);plate=g.build_shapes(p)['BottomPlate']
 for shape in BUMPER_SHAPES:
  for feature,recess in ((5.,1.),(90.,90.)):
   q=replace(p,FlexBumperShape=shape,FlexBumperTipWidth=feature,FlexBumperRecess=recess,FlexBumperLipReach=8.)
   s=front_bumper(q,{'BottomPlate':plate});assert s.isValid() and len(s.Solids)==1,(shape,feature,recess)
   assert s.common(plate).Volume<1e-6
   mesh=MeshPart.meshFromShape(Shape=s,LinearDeflection=.08,AngularDeflection=.2,Relative=False);assert mesh.isSolid(),(shape,feature,'mesh')
   checks.append([shape,feature,recess,'valid connected shoe and closed mesh'])
 full=front_bumper(p,{'BottomPlate':plate});short=front_bumper(replace(p,FlexBumperLipReach=8.),{'BottomPlate':plate})
 assert short.Volume<full.Volume
 assert abs(short.BoundBox.ZMin-full.BoundBox.ZMin)<1e-6 and abs(short.BoundBox.YMin-full.BoundBox.YMin)<1e-6
 checks.append('Shorter lip removes only upper capture stock, retaining the sole reach')
except Exception:fail.append(traceback.format_exc());traceback.print_exc()
(out/'bumper_controls.json').write_text(json.dumps(dict(checks=checks,failures=fail),indent=2));print(len(checks),fail,flush=True)
