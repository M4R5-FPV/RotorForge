"""Forward camera skirt must preserve the original FC/arm and wire clearance."""
import os,sys,json,traceback,time
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App,Part,MeshPart
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.geometry import build_shapes
from freecad.rotorforge.protection_layout import guard_layout
from freecad.rotorforge.flex_geometry import printable_flex
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(exist_ok=True,parents=True);checks=[];failures=[]
p=Parameters(FPVEnabled=True,FlexSideGuards=True,FlexGuardCloseFront=True,FlexGuardStyle='Solid',FlexGuardClearance=0.)
for name,q in [('three',p),('sloped',replace(p,TopReachMode='Custom',TopFrontReach=60.,CameraTopRearOffset=5.)),('access',replace(p,FlexGuardWireEnabled=True,FlexGuardUSBEnabled=True,FlexGuardUSBY=-6.))]:
 try:
  start=time.monotonic();shapes=build_shapes(q);g=guard_layout(q)[0]
  for role in ('ElectronicsGuardLeft','ElectronicsGuardRight'):
   s=shapes[role];assert s.isValid() and len(s.Solids)==1
   probe=Part.makeBox(200,g['front']-10-q.StackOffsetY,3,App.Vector(-100,q.StackOffsetY,3.))
   assert s.common(probe).Volume<1e-6,(role,s.common(probe).Volume)
   assert s.common(Part.makeBox(200,3,3,App.Vector(-100,g['front']+6,3.))).Volume>1
   if name=='three':
    flat=printable_flex(s,role);step=out/(role+'.step');flat.exportStep(str(step));restored=Part.Shape();restored.read(str(step));assert restored.isValid() and len(restored.Solids)==1 and abs(restored.Volume-flat.Volume)<.01
    mesh=MeshPart.meshFromShape(Shape=flat,LinearDeflection=.12,AngularDeflection=.3,Relative=False);assert mesh.isSolid();mesh.write(str(out/(role+'.stl')))
  if name=='three':
   parts=[]
   for role in ('BottomPlate','MidPlate','TopPlate','CameraMountLeft','CameraMountRight','ElectronicsGuardLeft','ElectronicsGuardRight'):
    s=shapes[role].copy()
    if role=='TopPlate':s.translate(App.Vector(0,0,14))
    vertices,faces=s.tessellate(.18);parts.append(dict(role=role,vertices=[tuple(v) for v in vertices],faces=faces))
   (out/'closure_scene.json').write_text(json.dumps(parts))
  checks.append(dict(name=name,seconds=round(time.monotonic()-start,2)));print('PASS',name,flush=True)
 except Exception:failures.append(dict(name=name,error=traceback.format_exc()));traceback.print_exc()
(out/'revision0661.json').write_text(json.dumps(dict(checks=checks,failures=failures),indent=2));print('DONE',len(checks),len(failures),flush=True)
