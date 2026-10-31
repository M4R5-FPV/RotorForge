"""Native closure geometry, new vent cutters and editor/saved-frame checks."""
import sys,os,json,traceback,time
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import FreeCAD as App,Part
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge.geometry import build_shapes
from freecad.rotorforge.protection_layout import guard_layout,closure_profile,vent_polygon
from freecad.rotorforge.flex_options import GUARD_VENT_SHAPES
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(exist_ok=True,parents=True);checks=[];failures=[]
p=Parameters(FPVEnabled=True,FlexSideGuards=True,FlexGuardCloseFront=True,FlexGuardStyle='Solid',FlexGuardClearance=0.)
# One physical print solid per side; the exact build also checks carbon,
# reference electronics, camera and actual metal-post collisions.
cases=[('three',p),('two_vents',replace(p,PlateDesign='2 plates',StandoffHeight=33.,FlexGuardStyle='Vented',FlexGuardVentShape='Shields',FlexGuardFCVentShape='Teardrops')),('sloped',replace(p,TopReachMode='Custom',TopFrontReach=60.,CameraTopRearOffset=5.))]
cases.append(('two_access',replace(p,PlateDesign='2 plates',StandoffHeight=33.,FlexGuardStyle='Vented',FlexGuardVentShape='Shields',FlexGuardFCVentShape='Teardrops',FlexGuardUSBEnabled=True,FlexGuardUSBY=-6.,FlexGuardWireEnabled=True)))
for name,q in cases:
 try:
  t=time.monotonic();shapes=build_shapes(q);guards={r:s for r,s in shapes.items() if r.startswith('ElectronicsGuard')}
  assert len(guards)==2 and all(s.isValid() and len(s.Solids)==1 for s in guards.values())
  for r,s in guards.items():
   assert s.BoundBox.YMax>=max(y for z,y in closure_profile(q,guard_layout(q)[0])['sections'])-.01,(r,s.BoundBox)
   assert s.BoundBox.ZMin<=q.BottomThickness+.01
  if name=='three':
   scenes=[];parts=[]
   for role in ('BottomPlate','MidPlate','TopPlate','CameraMountLeft','CameraMountRight','ElectronicsGuardLeft','ElectronicsGuardRight'):
    s=shapes[role].copy()
    if role=='TopPlate':s.translate(App.Vector(0,0,14))
    vertices,faces=s.tessellate(.18);parts.append(dict(role=role,vertices=[tuple(v) for v in vertices],faces=faces))
   (out/'closure_scene.json').write_text(json.dumps(parts))
   for r,s in guards.items():s.exportBrep(str(out/(r+'.brep')))
  checks.append(dict(name=name,seconds=round(time.monotonic()-t,2),volumes={r:s.Volume for r,s in guards.items()}));print('PASS',name,checks[-1]['seconds'],flush=True)
 except Exception:failures.append(dict(name=name,error=traceback.format_exc()));traceback.print_exc()
try:
 # All new profiles must form real open passages through native stock.
 for name in GUARD_VENT_SHAPES[6:]:
  pts=vent_polygon(dict(shape=name,width=10.,height=6.));vs=[App.Vector(-3,y,z) for y,z in pts];tool=Part.Face(Part.makePolygon(vs+[vs[0]])).extrude(App.Vector(6,0,0));slab=Part.makeBox(2,20,12,App.Vector(-1,-10,-6));cut=slab.cut(tool)
  assert cut.isValid() and len(cut.Solids)==1 and 0<cut.Volume<slab.Volume
 checks.append(dict(name='Ten vent profiles cut native stock and preserve a connected panel'));print('PASS CUTTERS',flush=True)
except Exception:failures.append(dict(name='Cutters',error=traceback.format_exc()))
try:
 from freecad.rotorforge.document import ensure_parameter_properties,set_parameters,read_parameters
 d=App.newDocument('SideClosure066');o=d.addObject('App::FeaturePython','FrameParameters');ensure_parameter_properties(o);set_parameters(o,p);assert read_parameters(o)==p
 d.saveAs(str(out/'ClosureParameters.FCStd'));App.closeDocument(d.Name);d=App.openDocument(str(out/'ClosureParameters.FCStd'));assert read_parameters(d.getObject('FrameParameters'))==p;App.closeDocument(d.Name)
 checks.append(dict(name='New closure settings persist in native FreeCAD properties'));print('PASS SAVE',flush=True)
except Exception:failures.append(dict(name='Native settings',error=traceback.format_exc()));traceback.print_exc()
(out/'revision066.json').write_text(json.dumps(dict(checks=checks,failures=failures),indent=2));print('DONE',len(checks),len(failures),flush=True)
