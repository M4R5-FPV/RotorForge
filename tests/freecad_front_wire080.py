"""Front exits traverse guard steps while retaining bearing stock and closed meshes."""
import sys,os,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
import FreeCAD as App,Part,MeshPart
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge import geometry as g
from freecad.rotorforge.protection_layout import guard_layout
from freecad.rotorforge.mesh_cleanup import weld_micro_seams
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True);checks=[];fail=[]
try:
 for close in (False,True):
  p=Parameters(FPVEnabled=True,StandoffHeight=35.,FlexSideGuards=True,FlexGuardExtendFront=True,FlexGuardCloseFront=close,FlexGuardWireEnabled=False,FlexGuardWirePairs='Front',FlexGuardClearance=0.)
  stock=g.build_shapes(p);layouts=guard_layout(p)
  for y in (18.,20.,23.,24.,25.,30.,36.,40.,43.,46.):
   q=replace(p,FlexGuardWireEnabled=True,FlexGuardWireFrontY=y);parts=g.build_shapes(q)
   for layout in layouts:
    role=layout['role'];shape=parts[role];assert shape.isValid() and len(shape.Solids)==1
    assert shape.Volume<stock[role].Volume-1e-5,(close,y,role,'no effective opening')
    removed=stock[role].cut(shape)
    radius=(p.StandoffDiameter+p.FlexGuardFit)/2+p.FlexGuardWall
    for stand,(low,high) in zip(layout['stands'],layout['bands']):
     band=Part.makeCylinder(radius,high-low,App.Vector(*stand['point'],low))
     assert removed.common(band).Volume<1e-6,(close,y,role,'grip removed')
    if y in (24.,40.,46.):
     mesh=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.08,AngularDeflection=.2,Relative=False);mesh=weld_micro_seams(mesh);assert mesh.isSolid(),(close,y,role,'mesh')
   (out/'progress.json').write_text(json.dumps(dict(close=close,y=y)))
   checks.append(('Closed forward guard' if close else 'Upper front strip')+' at Y '+str(y))
  g.build_for_update(q);r=replace(q,FlexGuardWireFrontY=42.);g.build_for_update(r);report=g.build_report(r)
  assert set(report['rebuilt'])<={'ElectronicsGuardLeft','ElectronicsGuardRight','FrameCGMarker'},report
  checks.append('Moving front pocket reuses carbon and guard base: '+repr(report['rebuilt']))
except Exception:fail.append(traceback.format_exc());traceback.print_exc()
(out/'front_wire.json').write_text(json.dumps(dict(checks=checks,failures=fail),indent=2));print(len(checks),fail,flush=True)
