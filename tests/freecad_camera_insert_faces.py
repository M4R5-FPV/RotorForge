"""Native rounded-window and mirrored single/double-flange regressions."""
import os,sys,json,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
import FreeCAD as App,Part,MeshPart
from freecad.rotorforge.flex_geometry import printable_flex
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge import geometry as g
from freecad.rotorforge.flex_geometry import camera_window
from freecad.rotorforge.fpv import camera_mounts
from freecad.rotorforge.camera_interface import lip_sides
from freecad.rotorforge.hardware_layout import hardware_layout
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True);checks=[];fail=[]
for outline in ('Rounded rectangle','Side plate outline'):
 base=Parameters(FPVEnabled=True,FlexCameraMode='Captured inserts',FlexInterfaceShape=outline,StandoffHeight=35.)
 areas={}
 for mode in ('Both sides','Outside only','Inside only'):
  p=replace(base,FlexInsertLipSide=mode)
  try:
   shapes=g.build_shapes(p)
   for sign,mount,role in zip((-1,1),camera_mounts(p),('CameraPadLeft','CameraPadRight')):
    pad=shapes[role];assert pad.isValid() and len(pad.Solids)==1
    mesh=MeshPart.meshFromShape(Shape=printable_flex(pad,role),LinearDeflection=.08,AngularDeflection=.2,Relative=False)
    assert mesh.isSolid(),role+' insert mesh is open'
    a,b=mount['plate_x'];window=camera_window(p,a,b-a)
    assert window.isValid() and any(isinstance(e.Curve,Part.Circle) for e in window.Edges)
    # Rounded through-window is preserved in the manufactured carbon profile.
    flat=g.flat_plate_shape(shapes[mount['role']],mount['role'],p)
    assert any(isinstance(e.Curve,Part.Circle) for e in flat.Edges)
    extension=(a-pad.BoundBox.XMin) if sign<0 else (pad.BoundBox.XMax-b)
    assert abs(extension-(max(.8,p.FlexPadThickness/2) if lip_sides(p)[1] else 0.))<1e-6
    # The contact region is still soft in every choice, but only selected
    # inner lips extend laterally beyond the opening.
    inner=b if sign<0 else a;face=sign*(p.CameraWidth/2-p.FlexPadPreload);x=(inner+face)/2
    wires=pad.slice(App.Vector(1,0,0),x)
    areas[(mode,sign)]=Part.makeFace(wires,'Part::FaceMakerBullseye').Area
   assert camera_mounts(p)==camera_mounts(base)
   specs=[s for s in hardware_layout(p) if s['group']=='Camera screws']
   for s in specs:
    mount=camera_mounts(p)[0 if s['owner'].endswith('Left') else 1]
    outer=max(abs(x) for x in mount['plate_x'])
    assert abs(abs(s['point'][0])-outer-(max(.8,p.FlexPadThickness/2) if lip_sides(p)[1] else 0.))<1e-6
   checks.append(outline+' / '+mode)
  except Exception:fail.append(dict(case=outline+' / '+mode,error=traceback.format_exc()));traceback.print_exc()
 if not fail:
  for sign in (-1,1):
   assert areas[('Both sides',sign)]>areas[('Outside only',sign)]
   assert abs(areas[('Both sides',sign)]-areas[('Inside only',sign)])<1e-6
(out/'insert_faces.json').write_text(json.dumps(dict(checks=checks,failures=fail),indent=2))
print(checks,fail,flush=True)
