"""Bell/prop contact, M5 engagement, feet, winding height and frame-axis pose."""
import sys,os,json,traceback,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App,Part
from freecad.rotorforge.detailed_references import motor_model,prop_model,detailed_reference
from freecad.rotorforge.reference_options import *
from freecad.rotorforge.parameters import Parameters,arm_layouts
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(exist_ok=True,parents=True);checks=[];fail=[]
try:
 for d,h,prop_d in ((12.,7.,40.),(28.,16.,127.),(40.,22.,254.)):
  motor,_=motor_model(d,h);prop,_=prop_model(prop_d);hub=prop.Solids[0]
  assert abs(hub.BoundBox.ZMin)<1e-6 and abs(hub.BoundBox.ZLength-6)<1e-6
  prop.translate(App.Vector(0,0,h));assert motor.common(prop).Volume<1e-5,(d,'interference',motor.common(prop).Volume)
  assert abs(motor.BoundBox.ZMax-shaft_top(h))<1e-6
  # M5 shaft is continuous through the hub and beyond the locknut.
  core=Part.makeCylinder(2.49,12.,App.Vector(0,0,h));assert core.cut(motor).Volume<1e-6
  assert motor.Solids[1].BoundBox.ZMax>=h*.89
  assert abs(motor.Solids[1].BoundBox.ZMin-h*.30)<1e-6
  support=motor.Solids[14]
  assert abs(support.BoundBox.ZMin-motor.Solids[0].BoundBox.ZMax)<1e-6
  assert abs(support.BoundBox.ZMax-motor.Solids[1].BoundBox.ZMin)<1e-6
  assert len(motor.Solids[0].fuse(support).fuse(motor.Solids[1]).Solids)==1
  for j in range(4):
   a=j*math.pi/2;tool=Part.makeCylinder(1.6+.49,h,App.Vector(d*.375*math.cos(a),d*.375*math.sin(a),0))
   assert support.common(tool).Volume<1e-6
  assert all(s.BoundBox.ZMax>=h*.91 for s in motor.Solids[2:14])
  assert all(s.BoundBox.ZMin>h*.30 and s.BoundBox.ZMin>motor.Solids[0].BoundBox.ZMax for s in motor.Solids[2:14])
  # Rounded feet have radial gaps at their lower face, not a circular flange.
  disc=Part.makeCylinder(d*.4,.1,App.Vector(0,0,.1));assert disc.cut(motor.Solids[0]).Volume>.01
  checks.append([d,h,prop_d,'6 mm hub seated; M5 through shaft; nut above; open feet; tall core/windings'])
 for layout in ('4-hole bolt circle','3-hole bolt circle'):
  p=Parameters(DetailedMotorReferences=True,MotorPadRotation=23.,MotorHoleRotation=17.,MotorHoleLayout=layout)
  shape,cols=detailed_reference(p,'MotorEnvelopes');assert shape.isValid() and len(cols)==len(shape.Faces)
  per=len(shape.Solids)//4;feet=[shape.Solids[i*per] for i in range(4)];supports=[shape.Solids[i*per+14] for i in range(4)];base=feet[0].BoundBox.ZMin
  for arm in arm_layouts(p):
   for x,y in arm['motor_holes']:
    tool=Part.makeCylinder(p.MotorHoleDiameter/2-.01,1.,App.Vector(x,y,base+.1))
    assert all(tool.common(foot).Volume<1e-6 for foot in feet),(layout,x,y)
    keepout=Part.makeCylinder(p.MotorHoleDiameter/2+.49,p.MotorReferenceHeight,App.Vector(x,y,base))
    assert all(keepout.common(support).Volume<1e-6 for support in supports),(layout,'support screw clearance')
  checks.append([layout,'feet holes follow rotated motor pad and frame motor positions'])
except Exception:fail.append(traceback.format_exc());traceback.print_exc()
(out/'motor_assembly.json').write_text(json.dumps(dict(checks=checks,failures=fail),indent=2));print(len(checks),fail,flush=True)
