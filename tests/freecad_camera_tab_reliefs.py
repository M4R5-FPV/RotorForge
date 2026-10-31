"""Native CNC relief checks: radius, full tab stock, one solid, exports and caching."""
import sys,os,json,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from dataclasses import replace
import FreeCAD as App,Part
from freecad.rotorforge.parameters import Parameters
from freecad.rotorforge import geometry as g,document as d
from freecad.rotorforge.fpv import camera_mounts,camera_tab_reliefs
from freecad.rotorforge.exporters import export_package,profile_entities
out=Path(os.environ['ROTORFORGE_TEST_OUTPUT']);out.mkdir(parents=True,exist_ok=True)
checks=[]
for diameter in (1.,2.):
 for side in ('CameraMountLeft','CameraMountRight'):
  p=Parameters(FPVEnabled=True,CameraTabCutterDiameter=diameter)
  m=next(m for m in camera_mounts(p) if m['role']==side)
  old=g.camera_bracket(replace(p,CameraTabReliefs=False),m);new=g.camera_bracket(p,m)
  assert new.isValid() and len(new.Solids)==1
  thickness=m['plate_x'][1]-m['plate_x'][0]
  assert abs(old.Volume-new.Volume-8*math.pi*(diameter/2)**2/2*thickness)<1e-6
  for ys,z,h in ((m['tabs_y'],0,p.BottomThickness),(m['top_tabs_y'],m['z1'],p.TopThickness)):
   for y in ys:
    tab=Part.makeBox(thickness,p.CameraTabLength,h,App.Vector(m['plate_x'][0],y-p.CameraTabLength/2,z))
    assert tab.cut(new).Volume<1e-7
  flat=g.flat_plate_shape(new,side,p)
  assert flat.isValid() and any(edge.Curve.__class__.__name__=='Circle' and abs(edge.Curve.Radius-diameter/2)<1e-7 for edge in flat.Edges)
  checks.append([diameter,side])
for mode in ('2 plates','3 plates'):
 p=Parameters(FPVEnabled=True,PlateDesign=mode,StandoffHeight=35,TopReachMode='Custom',TopFrontReach=60,TopRearReach=100,CameraBaseMode='Custom',CameraBaseFrontExtension=3,CameraBaseRearExtension=2)
 doc=App.newDocument();frame=d.create_frame(p,doc)
 parts=d.component_objects(frame)
 for role in ('CameraMountLeft','CameraMountRight'):assert not parts[role].Shape.isNull()
 for role,obj in parts.items():
  if not obj.Shape.isNull():assert obj.Shape.isValid(),role
 folder=export_package(frame,out/mode.replace(' ','_'))
 assert (folder/'ExportInfo.json').exists()
 App.closeDocument(doc.Name);checks.append(mode+' sloped side plates and export')
p=Parameters(FPVEnabled=True,FlexCameraMode='Captured inserts',StandoffHeight=35)
assert g.build_shape(p,'CameraMountLeft').isValid();checks.append('captured inserts')
(out/'camera_reliefs.json').write_text(json.dumps({'checks':checks,'failures':[]},indent=2))
print('PASS',checks,flush=True)
